from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import connect_db, close_db
from app.routers.parse import router as parse_router
from app.routers.users import router as users_router
from app.routers.calendar import router as calendar_router
from app.routers.user_data import router as user_data_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="Syllabus to Calendar API",
    description="AI-powered syllabus parser and autonomous study plan generator",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(parse_router)
app.include_router(users_router)
app.include_router(calendar_router)
app.include_router(user_data_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
