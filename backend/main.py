from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=True)

try:
    from .pipeline import is_mock_mode, run_pipeline, run_pipeline_events, stream_pipeline, using_mock_agents
except ImportError:  # Allows `uvicorn main:app` from inside backend/.
    from pipeline import is_mock_mode, run_pipeline, run_pipeline_events, stream_pipeline, using_mock_agents  # type: ignore


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("truthnet.main")

MAX_CLAIM_CHARS = 8_000
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(
    title="TruthNet API",
    description="4-agent adversarial fact-checking pipeline with optional SSE streaming.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NoCacheStaticFiles(StaticFiles):
    """Make browsers revalidate frontend files so edits show up on a normal refresh."""

    async def get_response(self, path: str, scope):  # type: ignore[override]
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response


if FRONTEND_DIR.exists():
    app.mount("/frontend", NoCacheStaticFiles(directory=FRONTEND_DIR), name="frontend")


class FactCheckRequest(BaseModel):
    claim: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=MAX_CLAIM_CHARS,
        description="Backward-compatible claim field.",
    )
    user_input: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=MAX_CLAIM_CHARS,
        description="Raw claim, headline, or article excerpt to fact-check.",
    )

    @model_validator(mode="after")
    def require_claim_text(self) -> "FactCheckRequest":
        if not (self.user_input or self.claim):
            raise ValueError("Provide either 'user_input' or 'claim'.")
        return self

    @property
    def text(self) -> str:
        return (self.user_input or self.claim or "").strip()


@app.get("/")
async def root_health_check() -> Dict[str, object]:
    return {
        "status": "ok",
        "service": "TruthNet",
        "version": "2.0.0",
        "mock_mode": is_mock_mode(),
        "using_mock_agents": using_mock_agents(),
        "max_claim_chars": MAX_CLAIM_CHARS,
        "message": "POST /fact-check with {\"user_input\":\"...\"} for SSE or {\"claim\":\"...\"} for JSON.",
    }


@app.get("/app")
async def frontend_app() -> FileResponse:
    index_file = FRONTEND_DIR / "TruthNet.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend files are not installed.")
    return FileResponse(index_file, headers={"Cache-Control": "no-cache"})


@app.get("/health")
async def health() -> Dict[str, object]:
    return await root_health_check()


@app.post("/fact-check")
async def fact_check(
    request: FactCheckRequest,
    stream: bool = Query(False, description="Force Server-Sent Events response."),
):
    logger.info("POST /fact-check - %d chars", len(request.text))

    # New Member 3 / React contract: { "user_input": "..." } streams SSE.
    # Existing terminal/API contract: { "claim": "..." } returns one JSON verdict.
    if stream or request.user_input is not None:
        return StreamingResponse(
            stream_pipeline(request.text),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    try:
        return await run_pipeline(request.text)
    except TimeoutError as exc:
        logger.warning("Pipeline timed out: %s", exc)
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Pipeline failed.")
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}") from exc


def _sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/fact-check/stream")
async def fact_check_stream(
    claim: str = Query(..., min_length=1),
) -> StreamingResponse:
    async def event_generator():
        async for item in run_pipeline_events(claim):
            yield _sse(item["event"], item["data"])

    return StreamingResponse(event_generator(), media_type="text/event-stream")
