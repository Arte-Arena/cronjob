# app/api.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.rocketry_routes import router as rocketry_router
from app.routes.scheduler_routes import router as scheduler_router

app = FastAPI(
    title="Rocketry with FastAPI",
    description="This is a REST API for a scheduler."
)

ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "https://cronjob.spacearena.net",
    "https://www.spacearena.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra rotas
@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

app.include_router(rocketry_router)
app.include_router(scheduler_router)


