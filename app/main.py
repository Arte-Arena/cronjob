# app/main.py

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

import asyncio
import logging

import uvicorn
from redbird.logging import RepoHandler
from redbird.repos import CSVFileRepo
from rocketry.log import MinimalRecord

from app.api import app
from app.rocketry_app import app_rocketry
from app.scheduler import load_schedules  # 🔥 IMPORT ADICIONADO

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("rocketry.task")
os.makedirs("logs", exist_ok=True)
handler = RepoHandler(repo=CSVFileRepo(filename="logs/tasks.csv", model=MinimalRecord))
logger.addHandler(handler)

class Server(uvicorn.Server):
    def handle_exit(self, sig, frame):
        app_rocketry.session.shut_down()
        return super().handle_exit(sig, frame)

async def main():
    # 🔥 CARREGA TAREFAS AGENDADAS NA INICIALIZAÇÃO
    logging.info("🚀 Iniciando aplicação...")
    await load_schedules()
    
    api = asyncio.create_task(
        Server(config=uvicorn.Config(app, loop="asyncio", host="0.0.0.0", port=8003)).serve()
    )
    scheduler = asyncio.create_task(app_rocketry.serve())
    await asyncio.wait([api, scheduler])

if __name__ == "__main__":
    logger.addHandler(logging.StreamHandler())
    asyncio.run(main())


