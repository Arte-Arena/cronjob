# app/routes/rocketry_routes.py

import time
from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from redbird.oper import in_, between, greater_equal

from app.rocketry_app import session  # agora vem de app.rocketry_app

router = APIRouter(prefix="/rocketry", tags=["rocketry"])


class Task(BaseModel):
    name: str
    description: Optional[str]
    priority: int

    start_cond: str
    end_cond: str
    timeout: Optional[int]

    disabled: bool
    force_termination: bool
    force_run: bool

    status: Optional[str]
    is_running: bool
    last_run: Optional[datetime]
    last_success: Optional[datetime]
    last_fail: Optional[datetime]
    last_terminate: Optional[datetime]
    last_inaction: Optional[datetime]
    last_crash: Optional[datetime]


class Log(BaseModel):
    timestamp: Optional[datetime] = Field(alias="created")
    task_name: str
    action: str


@router.get("/session/config")
async def get_session_config():
    return session.config


@router.patch("/session/config")
async def patch_session_config(values: dict):
    for key, val in values.items():
        setattr(session.config, key, val)


@router.get("/session/parameters")
async def get_session_parameters():
    return session.parameters


@router.get("/session/parameters/{name}")
async def get_session_parameter(name: str):
    return session.parameters[name]


@router.put("/session/parameters/{name}")
async def put_session_parameter(name: str, value):
    session.parameters[name] = value


@router.delete("/session/parameters/{name}")
async def delete_session_parameter(name: str):
    del session.parameters[name]


@router.post("/session/shut_down")
async def shut_down_session():
    session.shut_down()


@router.get("/tasks", response_model=List[Task])
async def get_tasks():
    return [
        Task(
            start_cond=str(task.start_cond),
            end_cond=str(task.end_cond),
            status=task.status or "pending",
            is_running=task.is_running,
            **task.dict(exclude={"start_cond", "end_cond"})
        )
        for task in session.tasks
    ]


@router.get("/tasks/{task_name}")
async def get_task(task_name: str):
    return session[task_name]


@router.patch("/tasks/{task_name}")
async def patch_task(task_name: str, values: dict):
    task = session[task_name]
    for attr, val in values.items():
        setattr(task, attr, val)


@router.post("/tasks/{task_name}/disable")
async def disable_task(task_name: str):
    session[task_name].disabled = True


@router.post("/tasks/{task_name}/enable")
async def enable_task(task_name: str):
    session[task_name].disabled = False


@router.post("/tasks/{task_name}/terminate")
async def terminate_task(task_name: str):
    session[task_name].force_termination = True


@router.post("/tasks/{task_name}/run")
async def run_task(task_name: str):
    session[task_name].force_run = True


@router.get("/logs")
async def get_task_logs(
    action: Optional[List[Literal["run", "success", "fail", "terminate", "crash", "inaction"]]] = Query(default=[]),
    min_created: Optional[int] = None,
    max_created: Optional[int] = None,
    past: Optional[int] = None,
    limit: Optional[int] = None,
    task: Optional[List[str]] = Query(default=None),
):
    filter = {}
    if action:
        filter["action"] = in_(action)
    if (min_created or max_created) and not past:
        filter["created"] = between(min_created, max_created, none_as_open=True)
    elif past:
        filter["created"] = greater_equal(time.time() - past)
    if task:
        filter["task_name"] = in_(task)

    repo = session.get_repo()
    logs = repo.filter_by(**filter).all()
    if limit:
        logs = logs[max(len(logs) - limit, 0):]
    logs = sorted(logs, key=lambda log: log.created, reverse=True)
    return [Log(**vars(log)) for log in logs]


@router.get("/task/{task_name}/logs")
async def get_logs_by_task(task_name: str,
    action: Optional[List[Literal["run", "success", "fail", "terminate", "crash", "inaction"]]] = Query(default=[]),
    min_created: Optional[int] = None,
    max_created: Optional[int] = None,
):
    filter = {}
    if action:
        filter["action"] = in_(action)
    if min_created or max_created:
        filter["created"] = between(min_created, max_created, none_as_open=True)

    return session[task_name].logger.filter_by(**filter).all()



