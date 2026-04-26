import logging
import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI", "")

client: AsyncIOMotorClient | None = None
db = None


async def connect_db():
    global client, db
    if not MONGODB_URI:
        logger.warning(
            "MONGODB_URI is not set — user data persistence is disabled. "
            "Set MONGODB_URI in your .env file to enable cloud storage of "
            "courses, task progress, and cold-call history."
        )
        return
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client.docket
    logger.info("Connected to MongoDB")
    await _ensure_indexes()


async def _ensure_indexes():
    """Create indexes for collections that need them."""
    if db is None:
        return
    await db.resources.create_index(
        [("uid", 1), ("course_name", 1)],
        unique=True,
        name="uid_course_unique",
    )


async def close_db():
    global client
    if client:
        client.close()


def get_db():
    return db
