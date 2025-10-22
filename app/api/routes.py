"""API routes for the Jenny main application."""
from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.strands.orchestrator import Orchestrator

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


@router.post("/orchestrate", response_model=OrchestrateResponse)
async def orchestrate(request: OrchestrateRequest) -> OrchestrateResponse:
    """Route the prompt through the orchestrator pipeline."""

    orchestrator = Orchestrator()
    try:
        result = await orchestrator.run(request.prompt)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return OrchestrateResponse(**result)
