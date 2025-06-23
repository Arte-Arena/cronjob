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
    send_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))

@router.post("/v1/space-desk/message")
async def schedule_message(payload: CreateMessageRequest):
    print("[schedule_message] Recebido payload:", payload.dict())
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
    print("[schedule_message] Documento a ser inserido no MongoDB:", doc)
    try:
        result = await db.scheduled_messages.insert_one(doc)
        print("✅ Inserido no MongoDB:", result.inserted_id)
        count = await db.scheduled_messages.count_documents({})
        print("📦 Total após insert:", count)
    except Exception as e:
        print("❌ Erro ao inserir no MongoDB:", e)

    async def send_task():
        payload_to_send = {
            "to": payload.to,
            "type": payload.type,
            "body": payload.body,
            "templateName": payload.templateName,
            "params": [param.dict() for param in payload.params],
            "userId": payload.userId
        }
        print("[send_task] Enviando payload para API externa:", payload_to_send)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post("https://api.erp.spacearena.net/v1/space-desk/message", json=payload_to_send)
                print(f"[send_task] Resposta da API externa: status={response.status_code}, body={response.text}")
            update_result = await db.scheduled_messages.update_one(
                {"_id": result.inserted_id},
                {"$set": {"status": "sent", "sent_at": datetime.now(timezone.utc)}}
            )
            print(f"[send_task] Status atualizado no MongoDB para 'sent'. Matched: {update_result.matched_count}, Modified: {update_result.modified_count}")
        except Exception as e:
            print("❌ Erro ao enviar mensagem ou atualizar status:", e)

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
