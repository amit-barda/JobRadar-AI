from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .config import settings
from .database import init_db
from .routers import auth, jobs, sources, cvs, matches, interviews, dashboard, cover_letter

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield

app = FastAPI(
    title="JobRadar AI",
    description="AI-powered job tracking for Product and Project Managers",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(sources.router, prefix="/api/v1/sources", tags=["sources"])
app.include_router(cvs.router, prefix="/api/v1/cvs", tags=["cvs"])
app.include_router(matches.router, prefix="/api/v1/matches", tags=["matches"])
app.include_router(interviews.router, prefix="/api/v1/interviews", tags=["interviews"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(cover_letter.router, prefix="/api/v1/cover-letter", tags=["cover-letter"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "JobRadar AI"}

@app.get("/")
def root():
    return {"message": "JobRadar AI API", "docs": "/docs"}
