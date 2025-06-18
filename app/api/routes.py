# app/api/routes.py

from fastapi import APIRouter
from api.schemas import MessageScheduleRequest
from api.db import db
from datetime import datetime

router = APIRouter()

@router.post("/schedule-message")
async def schedule_message(payload: MessageScheduleRequest):
    collection = db["scheduled_messages"]

    doc = {
        "clients": payload.clients,
        "template": payload.template,
        "send_at": payload.send_at,
        "created_at": datetime.utcnow(),
        "status": "scheduled"
    }

    result = await collection.insert_one(doc)
    return {
        "status": "scheduled",
        "id": str(result.inserted_id),
        "count": len(payload.clients)
    }
