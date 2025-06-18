# app/main.py

"""
This file combines the two applications.
"""

import asyncio
import logging

import uvicorn

from app.api import app as app_fastapi
from app.scheduler import app as app_rocketry

from redbird.repos import CSVFileRepo
from rocketry.log import MinimalRecord
from redbird.logging import RepoHandler
import logging

repo = CSVFileRepo(filename="logs/tasks.csv", model=MinimalRecord)
handler = RepoHandler(repo=repo)
logger = logging.getLogger("rocketry.task")
logger.addHandler(handler)

app = app_fastapi

class Server(uvicorn.Server):
    """Customized uvicorn.Server
    
    Uvicorn server overrides signals and we need to include
    Rocketry to the signals."""
    def handle_exit(self, sig: int, frame) -> None:
        app_rocketry.session.shut_down()
        return super().handle_exit(sig, frame)

async def load_schedules():
    pending = db.scheduled_messages.find({"status": "scheduled"})
    async for doc in pending:
        # criar FuncTask similar ao schedule_message
        ...
        app_rocketry.session.add_task(task)

@app.setup()
async def on_startup():
    await load_schedules()

async def main():
    "Run Rocketry and FastAPI"
    server = Server(config=uvicorn.Config(app_fastapi, workers=1, loop="asyncio"))

    api = asyncio.create_task(server.serve())
    sched = asyncio.create_task(app_rocketry.serve())

    await asyncio.wait([sched, api])

if __name__ == "__main__":
    # Print Rocketry's logs to terminal
    logger = logging.getLogger("rocketry.task")
    logger.addHandler(logging.StreamHandler())

    # Run both applications
    asyncio.run(main())
