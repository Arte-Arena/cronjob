import pytest
from httpx import AsyncClient, ASGITransport
from app.api import app

@pytest.mark.asyncio
async def test_healthcheck():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/healthcheck")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


