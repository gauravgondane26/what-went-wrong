from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS, HTTP_TIMEOUT_SECONDS
from app.routers import analysis, competitions, matches
from app.services import cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(
        timeout=HTTP_TIMEOUT_SECONDS,
        headers={"User-Agent": "what-went-wrong/0.1"},
        follow_redirects=True,
    )
    yield
    await app.state.http_client.aclose()


app = FastAPI(title="What Went Wrong", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(competitions.router, prefix="/api/v1")
app.include_router(matches.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health():
    return {
        "status": "ok",
        "cache_entries": cache.total_entries(),
    }
