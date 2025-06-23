# app/scheduler.py
"""
Carrega mensagens com status='scheduled' do MongoDB e registra-as como tarefas
dinâmicas no Rocketry.  Mantém uma única instância de Rocketry (importada de
app.rocketry_app) e evita circular import.

➜  Uso:
     from app.scheduler import load_schedules
     await load_schedules()        # chamado no boot em app/main.py
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Any

import httpx
from rocketry.conds import cron

from app.db import db
from app.rocketry_app import app_rocketry

logger = logging.getLogger("scheduler")


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #
def _build_cron_expression(send_at: datetime) -> str:
    """Retorna expressão cron no formato '<min> <hour> <day> <month> *'."""
    send_at_utc = send_at.astimezone(timezone.utc)
    return f"{send_at_utc.minute} {send_at_utc.hour} {send_at_utc.day} {send_at_utc.month} *"


def _task_already_registered(name: str) -> bool:
    """Verifica se já existe tarefa com esse nome na sessão."""
    return any(task.name == name for task in app_rocketry.session.tasks)


# --------------------------------------------------------------------------- #
# Registro dinâmico                                                           #
# --------------------------------------------------------------------------- #
def register_send_task(doc: Dict[str, Any]) -> None:
    """
    Cria e registra uma Rocketry task responsável por enviar a mensagem
    representada por `doc`.

    Esta função **não** deve ser chamada diretamente fora deste módulo;
    use sempre `load_schedules`.
    """
    task_name = f"task_{doc['_id']}"
    if _task_already_registered(task_name):
        logger.info("⚠️  Tarefa %s já estava registrada — ignorando duplicata.", task_name)
        return

    cron_exp = _build_cron_expression(doc["send_at"])

    # 1️⃣ Define a função que será executada
    async def send_task():  # noqa: WPS430 (nested function OK aqui)
        task_logger = logging.getLogger(f"task.{task_name}")
        payload = {
            "to": doc["to"],
            "type": doc["type"],
            "body": doc["body"],
            "templateName": doc.get("template"),
            "params": doc["params"],
            "userId": doc["userId"],
        }

        try:
            task_logger.info("🚀 Enviando payload para API externa")
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.erp.spacearena.net/v1/space-desk/message",
                    json=payload,
                )
            task_logger.info("✅ API respondeu status=%s", resp.status_code)

            # Atualiza status no MongoDB
            await db.scheduled_messages.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "status": "sent",
                    "sent_at": datetime.now(timezone.utc),
                    "response_status": resp.status_code,
                }},
            )
        except Exception as exc:  # noqa: BLE001
            task_logger.exception("❌ Falha ao enviar mensagem: %s", exc)
            await db.scheduled_messages.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "status": "failed",
                    "error": str(exc),
                    "failed_at": datetime.now(timezone.utc),
                }},
            )

    # 2️⃣ Registra dinamicamente na sessão Rocketry
    app_rocketry.session.create_task(
        func=send_task,
        name=task_name,
        start_cond=cron(cron_exp),
        execution="async",
    )

    logger.info("📌 Registrado %s para cron '%s'", task_name, cron_exp)


# --------------------------------------------------------------------------- #
# API pública                                                                  #
# --------------------------------------------------------------------------- #
async def load_schedules() -> None:
    """
    Itera pela collection `scheduled_messages` buscando documentos com
    `status='scheduled'` e registra cada um como tarefa Rocketry.
    """
    logger.info("🔄 Carregando tarefas agendadas do MongoDB…")
    count = 0
    async for doc in db.scheduled_messages.find({"status": "scheduled"}):
        register_send_task(doc)
        count += 1

    logger.info("✅ Carregamento concluído: %d tarefas registradas.", count)
