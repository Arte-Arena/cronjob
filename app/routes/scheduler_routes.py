# app/routes/scheduler_routes.py

from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import List, Optional, Literal

from app.db import db
from app.scheduler import register_send_task
from app.rocketry_app import app_rocketry

router = APIRouter(tags=["scheduler"])


class MessageParam(BaseModel):
    type: Literal["text"]
    text: str

class CreateMessageRequest(BaseModel):
    to: Optional[str] = None
    clients: Optional[List[str]] = None
    body: str
    type: str
    templateName: str
    params: List[MessageParam]
    userId: str
    send_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


@router.post("/v1/space-desk/message")
async def schedule_message(payload: CreateMessageRequest, request: Request):
    now_utc = datetime.now(timezone.utc)
    if payload.send_at < now_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'send_at' ({payload.send_at.isoformat()}) está no passado. Use um horário futuro."
        )
    auth_token = request.headers.get("authorization")
    scheduled_ids = []
    clients = payload.clients if payload.clients else ([payload.to] if payload.to else [])
    if not clients:
        raise HTTPException(400, detail="Deve ser informado pelo menos um destinatário (to ou clients).")
    for phone in clients:
        doc = {
            "to": phone,
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
        try:
            result = await db.scheduled_messages.insert_one(doc)
            scheduled_ids.append(str(result.inserted_id))
            register_send_task({**doc, "_id": result.inserted_id})
        except Exception as e:
            print("❌ Erro ao inserir/agendar:", e)

    return {
        "status": "scheduled",
        "scheduled_ids": scheduled_ids,
        "template": payload.templateName,
        "userId": payload.userId,
    }
