# app/api/db.py

from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = "cronjob"

client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB_NAME]