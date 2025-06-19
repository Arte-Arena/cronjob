import pytest
import httpx
from httpx import AsyncClient, ASGITransport, Response, Request
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from app.api import app
from app.db import db

@pytest.mark.asyncio
async def test_schedule_message_realistic(mocker):
    # Simula a resposta esperada da chamada HTTP externa
    mock_response = Response(
        status_code=200,
        request=Request("POST", "https://api.erp.local/send"),
        json={"ok": True}
    )

    # Salva o método original
    original_post = httpx.AsyncClient.post

    # Define side_effect que respeita a assinatura de método de instância
    async def mock_post(self, url, *args, **kwargs):
        if "api.erp.local/send" in url:
            return mock_response
        return await original_post(self, url, *args, **kwargs)

    # Aplica o patch
    mocker.patch("httpx.AsyncClient.post", new=mock_post)

    await db.scheduled_messages.delete_many({})

    payload = {
        "to": "683dc488b9010fa623304c97",
        "body": "Olá teste1, tudo bem?\n\nAqui é o(a) *teste2* do time comercial da *Arte Arena*. 🎨\nGostaria de agendar uma breve reunião (15 min) para apresentar nossas soluções de personalização. Você teria disponibilidade *amanhã às teste3*?\n\n",
        "type": "template",
        "templateName": "artearena_comercial_prospeccao",
        "params": [
            {"type": "text", "text": "teste1"},
            {"type": "text", "text": "teste2"},
            {"type": "text", "text": "teste3"}
        ],
        "userId": "user_teste_123",
        "send_at": (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/v1/space-desk/message", json=payload)

    print("RESPONSE TEXT:", response.text)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "scheduled"
    assert "id" in data

    doc = await db.scheduled_messages.find_one({"_id": ObjectId(data["id"])})
    assert doc is not None
    assert doc["status"] == "scheduled"
    assert doc["template"] == payload["templateName"]
    assert doc["userId"] == payload["userId"]
    assert doc["to"] == payload["to"]
    assert doc["body"] == payload["body"]
    assert doc["type"] == payload["type"]
    assert doc["params"] == payload["params"]

    assert "task" in data
    assert isinstance(data["id"], str)
    assert data["task"] is None or isinstance(data["task"], str)



