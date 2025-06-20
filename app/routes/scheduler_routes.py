from datetime import datetime, timezone
from typing import List, Optional, Literal

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.db import db
from rocketry import Rocketry

router = APIRouter(tags=["scheduler"])

app_rocketry = Rocketry()


class MessageParam(BaseModel):
    type: Literal["text"]  # Pode ser expandido no futuro
    text: str


class CreateMessageRequest(BaseModel):
    to: str
    body: str
    type: str  # e.g., 'template'
    templateName: str
    params: List[MessageParam]
    userId: str
    send_at: Optional[datetime] = Field(default_factory=lambda: datetime.utcnow())

@router.post("/v1/space-desk/message")
async def schedule_message(payload: CreateMessageRequest):
    doc = {
        "to": payload.to,
        "body": payload.body,
        "type": payload.type,
        "template": payload.templateName,
        "params": [param.dict() for param in payload.params],
        "userId": payload.userId,
        "send_at": payload.send_at,
        "status": "scheduled",
        "created_at": datetime.now(timezone.utc),
    }
    try:
        result = await db.scheduled_messages.insert_one(doc)
        print("✅ Inserido no MongoDB:", result.inserted_id)
        count = await db.scheduled_messages.count_documents({})
        print("📦 Total após insert:", count)
    except Exception as e:
        print("❌ Erro ao inserir no MongoDB:", e)

    async def send_task():
        async with httpx.AsyncClient() as client:
            await client.post("https://api.erp.local/send", json={
                "template": payload.templateName,
                "clients": [payload.to],
                "params": [param.dict() for param in payload.params]
            })
        await db.scheduled_messages.update_one(
            {"_id": result.inserted_id},
            {"$set": {"status": "sent", "sent_at": datetime.utcnow()}}
        )

    print("[schedule_message] tarefa agendada no banco, será executada pelo scheduler.")

    return {
        "status": "scheduled",
        "task": None,
        "id": str(result.inserted_id),
        "to": payload.to,
        "template": payload.templateName,
        "userId": payload.userId,
        "params": [param.dict() for param in payload.params]
    }
