from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_db

router = APIRouter(prefix="/api/users", tags=["users"])


class UserSignIn(BaseModel):
    uid: str
    email: str | None = None
    display_name: str | None = None
    photo_url: str | None = None


@router.post("/signin")
async def record_signin(data: UserSignIn):
    db = get_db()
    if db is None:
        return {
            "uid": data.uid,
            "email": data.email,
            "display_name": data.display_name,
            "last_sign_in": datetime.now(timezone.utc).isoformat(),
        }

    now = datetime.now(timezone.utc)
    result = await db.users.find_one_and_update(
        {"uid": data.uid},
        {
            "$set": {
                "email": data.email,
                "display_name": data.display_name,
                "photo_url": data.photo_url,
                "last_sign_in": now,
            },
            "$setOnInsert": {
                "uid": data.uid,
                "created_at": now,
            },
        },
        upsert=True,
        return_document=True,
    )
    return {
        "uid": result["uid"],
        "email": result.get("email"),
        "display_name": result.get("display_name"),
        "last_sign_in": result.get("last_sign_in"),
    }


@router.get("/{uid}")
async def get_user(uid: str):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=404, detail="User not found")

    user = await db.users.find_one({"uid": uid}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
