# app/scheduler.py

from __future__ import annotations
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

import httpx
from rocketry.conds import cron

from app.db import db
from app.rocketry_app import app_rocketry

logger = logging.getLogger("scheduler")


def _build_cron_expression(send_at: datetime) -> str:
    send_at_utc = send_at.astimezone(timezone.utc)
    return f"{send_at_utc.minute} {send_at_utc.hour} {send_at_utc.day} {send_at_utc.month} *"


def _task_already_registered(name: str) -> bool:
    return any(task.name == name for task in app_rocketry.session.tasks)


def register_send_task(doc: Dict[str, Any]) -> None:
    task_name = f"task_{doc['_id']}"
    if _task_already_registered(task_name):
        logger.info("⚠️  Tarefa %s já estava registrada — ignorando duplicata.", task_name)
        return

    cron_exp = _build_cron_expression(doc["send_at"])

    # --- Validação Rocketry: handler chamado 30 segundos antes do envio ---
    async def validate_before_send():
        now = datetime.now(timezone.utc)
        # Executa a validação só se estiver nos 30s antes do horário do envio
        if now < doc["send_at"] - timedelta(seconds=30):
            logger.info("⏳ Ainda não é o momento de validar (falta >30s).")
            return False  # Adia execução
        logger.info("🔎 Validando necessidade de envio para %s...", doc["to"])
        payload = {
            "to": doc["to"],
            "createdAt": doc["created_at"].isoformat(),
            "now": now.isoformat()
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.erp.spacearena.net/v1/space-desk/message/validate",
                    json=payload,
                    headers={"Authorization": doc.get("auth_token")} if doc.get("auth_token") else None
                )
                resp.raise_for_status()
                result = resp.json()
                logger.info("🔔 Resposta da validação: %s", result)
                return result.get("should_send", True)  # True para enviar, False para abortar
        except Exception as exc:
            logger.exception("Erro ao validar necessidade de envio: %s", exc)
            return True  # fallback: envia mesmo assim

    # --- Função de envio principal ---
    async def send_task():
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
            headers = {}
            if doc.get("auth_token"):
                headers["Authorization"] = doc["auth_token"]
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.erp.spacearena.net/v1/space-desk/message",
                    json=payload,
                    headers=headers if headers else None,
                )
            task_logger.info("✅ API respondeu status=%s", resp.status_code)
            await db.scheduled_messages.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "status": "sent",
                    "sent_at": datetime.now(timezone.utc),
                    "response_status": resp.status_code,
                }},
            )
        except Exception as exc:
            task_logger.exception("❌ Falha ao enviar mensagem: %s", exc)
            await db.scheduled_messages.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "status": "failed",
                    "error": str(exc),
                    "failed_at": datetime.now(timezone.utc),
                }},
            )

    # --- Registra Rocketry com validação before_run ---
    app_rocketry.session.create_task(
        func=send_task,
        name=task_name,
        start_cond=cron(cron_exp),
        execution="async",
        before_run=validate_before_send,
    )
    logger.info("📌 Registrado %s para cron '%s'", task_name, cron_exp)


async def load_schedules() -> None:
    logger.info("🔄 Carregando tarefas agendadas do MongoDB…")
    count = 0
    async for doc in db.scheduled_messages.find({"status": "scheduled"}):
        register_send_task(doc)
        count += 1
    logger.info("✅ Carregamento concluído: %d tarefas registradas.", count)



