"""Voice transcription utilities using Gemini Audio API."""
from __future__ import annotations

import asyncio
import os
from typing import Optional

import requests

DEFAULT_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-latest:transcribe"
)


class GeminiAudioClient:
    """Blocking HTTP client for Gemini audio transcription."""

    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.endpoint = os.getenv("GEMINI_AUDIO_ENDPOINT", DEFAULT_ENDPOINT)

    def transcribe(self, audio_url: str, language_code: Optional[str] = None) -> str:
        if not self.api_key:
            return f"[transcript unavailable] Received audio: {audio_url}"

        payload = {"audio_url": audio_url}
        if language_code:
            payload["language_code"] = language_code

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }
        response = requests.post(self.endpoint, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        transcript = (
            data.get("text")
            or data.get("transcript")
            or data.get("result", {}).get("transcript")
        )
        if not transcript:
            return "[no transcription returned]"
        return str(transcript)


async def transcribe_audio(audio_url: str, language_code: Optional[str] = None) -> str:
    """Asynchronously transcribe the given audio URL."""

    loop = asyncio.get_running_loop()
    client = GeminiAudioClient()
    return await loop.run_in_executor(None, client.transcribe, audio_url, language_code)


__all__ = ["transcribe_audio", "GeminiAudioClient"]
