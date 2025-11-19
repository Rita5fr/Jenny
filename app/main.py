"""Main FastAPI application for Jenny orchestrator."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, model_validator
import sentry_sdk

from app.core.db import init_pool
from app.services.memory_utils import add_memory, search_memory
from app.services.voice import transcribe_audio
from app.crew.crew import get_crew

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env", override=False)

SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(  # type: ignore[attr-defined]
        dsn=SENTRY_DSN,
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events."""
    # Startup
    init_pool()
    yield
    # Shutdown (if needed in the future)


app = FastAPI(title="Jenny", version="0.5.0", lifespan=lifespan)
crew = get_crew()


class QueryPayload(BaseModel):
    user_id: str = Field(..., min_length=1)
    text: Optional[str] = None
    voice_url: Optional[str] = None
    image_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def ensure_payload(self) -> "QueryPayload":
        if not (self.text or self.voice_url or self.image_url):
            raise ValueError("One of text, voice_url, or image_url must be provided")
        return self


class RememberPayload(BaseModel):
    user_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)


@app.get("/health")
async def health() -> dict[str, bool]:
    """Return a basic health response."""

    return {"ok": True}


@app.post("/ask")
async def ask(payload: QueryPayload) -> dict:
    """Process user query directly through CrewAI orchestrator."""

    try:
        user_id = payload.user_id

        # Handle different input types
        query_text = None

        if payload.text:
            query_text = payload.text
        elif payload.voice_url:
            # Transcribe voice
            query_text = await transcribe_audio(payload.voice_url)
            if not query_text:
                return {
                    "agent": "voice_transcription",
                    "reply": "I could not understand the audio. Could you type it instead?",
                }
        elif payload.image_url:
            return {
                "agent": "image_analysis",
                "reply": "Image messages are not yet supported. Please send text.",
            }

        if not query_text:
            raise ValueError("No valid input provided")

        # Process with CrewAI directly - it will use Mem0 for context
        response = await crew.process_query(
            query=query_text,
            user_id=user_id,
            context={"user_id": user_id, "metadata": payload.metadata or {}}
        )

        return response

    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/demo/remember")
async def remember(payload: RememberPayload) -> dict:
    """Directly add a memory via the memory agent."""

    return await add_memory(payload.text, payload.user_id)


@app.get("/demo/search")
async def demo_search(user_id: str, q: str, k: int = 5) -> dict:
    """Search stored memories via the memory agent."""

    if not user_id or not q:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id and q required")
    return await search_memory(q, user_id, k=k)
