from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.parse import router as parse_router

app = FastAPI(
    title="Syllabus to Calendar API",
    description="AI-powered syllabus parser and autonomous study plan generator",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(parse_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
