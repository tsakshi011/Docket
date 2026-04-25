import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "")

client: AsyncIOMotorClient | None = None
db = None


async def connect_db():
    global client, db
    if not MONGODB_URI:
        return
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client.docket


async def close_db():
    global client
    if client:
        client.close()


def get_db():
    return db
