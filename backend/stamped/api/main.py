from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from stamped.api.status import router as status_router
from stamped.api.tiles import router as tiles_router
from stamped.core.db import init_db
from stamped.core.events import bus

_FRONTEND_DIST = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
    yield


app = FastAPI(title="Stamped", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status_router, prefix="/api")
app.include_router(tiles_router)


@app.get("/api/events")
async def sse_events() -> StreamingResponse:
    q = bus.subscribe()
    return StreamingResponse(bus.stream(q), media_type="text/event-stream")


if _FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=_FRONTEND_DIST, html=True), name="frontend")
