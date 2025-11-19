"""API routes for the Jenny main application."""
from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.strands.orchestrator import Orchestrator  # Legacy - deprecated, use CrewAI

router = APIRouter(prefix="/api", tags=["orchestrator"])


class OrchestrateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="User prompt to process")


class OrchestrateResponse(BaseModel):
    prompt: str
    results: list[dict]


@router.get("/health", tags=["health"])
async def healthcheck() -> dict[str, str]:
    """Return a heartbeat response."""

    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{settings.mem0_base_url}/health")
            response.raise_for_status()
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mem0 service unavailable",
        ) from None
    return {"status": "ok"}


@router.post("/orchestrate")
async def orchestrate(request: OrchestrateRequest) -> dict:
    """Route the prompt through the orchestrator pipeline.

    DEPRECATED: This endpoint uses the legacy Orchestrator.
    For new code, use the /ask endpoint which uses CrewAI.
    """

    orchestrator = Orchestrator()
    try:
        result = await orchestrator.invoke(request.prompt, {"user_id": "api_user"})
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return result
