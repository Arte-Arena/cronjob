from app.db import db
from datetime import datetime
import httpx
from app.routes.rocketry_routes import app_rocketry

async def load_schedules():
    async for doc in db.scheduled_messages.find({"status": "scheduled"}):
        async def send_task(clients=doc["clients"], template=doc["template"], task_id=doc["_id"]):
            async with httpx.AsyncClient() as client:
                await client.post("https://api.erp.local/send", json={"template": template, "clients": clients})
            await db.scheduled_messages.update_one({"_id": task_id}, {"$set": {"status": "sent", "sent_at": datetime.utcnow()}})

        app_rocketry.task_factory.add(
            func=send_task,
            name=f"task_{doc['name']}",
            start_cond=f"once @ {doc['send_at'].strftime('%Y-%m-%d %H:%M')}"
        )


