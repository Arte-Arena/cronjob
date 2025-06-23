# app/scheduler.py
import logging
from datetime import datetime, timezone
import httpx

from app.db import db
from app.rocketry_app import app_rocketry

logger = logging.getLogger("scheduler")


def _register_send_task(doc):
    """Helper para registrar uma única tarefa no Rocketry"""
    task_name = f"task_{doc['_id']}"
    start_when = doc["send_at"].astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    @app_rocketry.task(name=task_name, start_cond=f"once @ {start_when}")
    async def send_task():
        payload = {
            "to": doc["to"],
            "type": doc["type"],
            "body": doc["body"],
            "templateName": doc["template"],
            "params": doc["params"],
            "userId": doc["userId"],
        }
        task_logger = logging.getLogger(f"task.{task_name}")
        try:
            task_logger.info("Enviando payload")
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.erp.spacearena.net/v1/space-desk/message",
                    json=payload,
                )
            await db.scheduled_messages.update_one(
                {"_id": doc["_id"]},
                {"$set": {"status": "sent",
                          "sent_at": datetime.now(timezone.utc),
                          "response_status": resp.status_code}},
            )
        except Exception as e:
            task_logger.error(f"Falha: {e}")
            await db.scheduled_messages.update_one(
                {"_id": doc["_id"]},
                {"$set": {"status": "failed",
                          "error": str(e),
                          "failed_at": datetime.now(timezone.utc)}},
            )

    logger.info(f"Registrado {task_name} para once @ {start_when}")


async def load_schedules():
    logger.info("Carregando tarefas agendadas do MongoDB…")
    async for doc in db.scheduled_messages.find({"status": "scheduled"}):
        _register_send_task(doc)
    logger.info("Carregamento concluído.")


