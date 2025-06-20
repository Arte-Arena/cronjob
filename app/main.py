# app/main.py

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

import asyncio
import logging

import uvicorn
from redbird.logging import RepoHandler
from redbird.repos import CSVFileRepo
from rocketry.log import MinimalRecord  # Pode deixar importado se quiser usar futuramente

from app.api import app
from app.rocketry_app import app_rocketry

logger = logging.getLogger("rocketry.task")
handler = RepoHandler(repo=CSVFileRepo(filename="logs/tasks.csv", model=MinimalRecord))
logger.addHandler(handler)


class Server(uvicorn.Server):
    def handle_exit(self, sig, frame):
        app_rocketry.session.shut_down()
        return super().handle_exit(sig, frame)


async def main():
    api = asyncio.create_task(Server(config=uvicorn.Config(app, loop="asyncio")).serve())
    scheduler = asyncio.create_task(app_rocketry.serve())
    await asyncio.wait([api, scheduler])


if __name__ == "__main__":
    logger.addHandler(logging.StreamHandler())
    asyncio.run(main())


