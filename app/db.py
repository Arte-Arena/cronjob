# app/db.py

from dotenv import load_dotenv
load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient
import os

client = AsyncIOMotorClient(os.getenv("MONGO_URI", "mongodb://mongo:27017"))
db = client[os.getenv("MONGO_DB", "cronjob")]

