from datetime import datetime, timezone
from typing import List, Optional, Literal

from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field

from app.db import db
from app.scheduler import register_send_task
from app.rocketry_app import app_rocketry

router = APIRouter(tags=["scheduler"])


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
async def schedule_message(payload: CreateMessageRequest, request: Request):

    # 📌 Validação de data/hora -----------------------------
    now_utc = datetime.now(timezone.utc)
    if payload.send_at < now_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'send_at' ({payload.send_at.isoformat()}) está no passado. "
                   f"Use um horário futuro."
        )
    # ----------------------------------------------------------

    # Captura o token do header Authorization
    auth_token = request.headers.get("authorization")

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
        "auth_token": auth_token,
    }
    print("[schedule_message] Documento a ser inserido no MongoDB:", doc)
    try:
        result = await db.scheduled_messages.insert_one(doc)
        print("✅ Inserido no MongoDB:", result.inserted_id)
        count = await db.scheduled_messages.count_documents({})
        print("📦 Total após insert:", count)
        # 🔥 registra imediatamente na sessão Rocketry
        register_send_task({**doc, "_id": result.inserted_id})
    except Exception as e:
        print("❌ Erro ao inserir no MongoDB:", e)

    return {
        "status": "scheduled",
        "task": str(result.inserted_id),
        "id": str(result.inserted_id),
        "to": payload.to,
        "template": payload.templateName,
        "userId": payload.userId,
        "params": [param.dict() for param in payload.params]
    }
