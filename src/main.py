"""Main Service"""

import logging
import os
from contextlib import asynccontextmanager
from logging.handlers import TimedRotatingFileHandler

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from tortoise import connections
from tortoise.exceptions import DBConnectionError
from plus_db_agent.manager import close, init

from src.config import (
    BASE_DIR,
    DATE_FORMAT,
    FORMAT,
    LOG_FILENAME,
    ORIGINS,
)
from src.scheduler.manager import ConnectionManager

if not os.path.exists(f"{BASE_DIR}/logs/"):
    os.makedirs(f"{BASE_DIR}/logs/")

file_handler = TimedRotatingFileHandler(LOG_FILENAME, when="midnight")
file_handler.suffix = "bkp"
logging.basicConfig(
    encoding="utf-8",
    level=logging.DEBUG,
    format=FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[file_handler],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager for the lifespan of the application."""
    logger.info("Service Version %s", app.version)
    # db connected
    await init()
    ConnectionManager().start_main_thread()
    yield
    await close()


appAPI = FastAPI(
    version="1.0.0",
    lifespan=lifespan,
)

appAPI.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@appAPI.get("/", tags=["Service"])
def root():
    """Redirect to docs"""
    return RedirectResponse(url="/docs")


@appAPI.get("/health", tags=["Service"])
async def health():
    """Health check"""
    try:
        await connections.get("default").execute_query("SELECT 1")
        return {"status": "ok"}
    except DBConnectionError:
        return {"status": "Database connection error"}


@appAPI.websocket("/scheduler/{clinic_id}/")
async def scheduler(websocket: WebSocket, clinic_id: int):
    """Websocket connection"""
    manager = ConnectionManager()
    await manager.connect(websocket, clinic_id, websocket.headers.get("authorization"))
