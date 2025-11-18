"""Conversation interface bridging transport channels with CrewAI orchestrator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.strands.agents.voice_agent import transcribe_audio
from app.strands.context_store import SessionSnapshot, SessionStore
from app.crew.crew import JennyCrew


@dataclass
class IncomingMessage:
    """Normalized representation of a user message."""

    user_id: str
    text: Optional[str] = None
    voice_url: Optional[str] = None
    image_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationInterface:
    """High-level interface for handling multi-modal user input."""

    def __init__(self, crew: JennyCrew, session_store: SessionStore) -> None:
        self._crew = crew
        self._sessions = session_store

    async def handle_message(self, message: IncomingMessage) -> Dict[str, Any]:
        """Dispatch a normalized message through the orchestrator pipeline."""

        if not message.user_id:
            raise ValueError("user_id is required to process a message")

        snapshot = await self._sessions.get_context(message.user_id)
        payload = {
            "user_id": message.user_id,
            "session": snapshot,
            "metadata": message.metadata or {},
        }

        if message.text:
            reply = await self._handle_text(message.text, payload)
        elif message.voice_url:
            reply = await self._handle_voice(message.voice_url, payload)
        elif message.image_url:
            reply = await self._handle_image(message.image_url, payload)
        else:
            raise ValueError("Message must contain text, voice, or image content.")

        await self._sessions.append_history(
            message.user_id,
            {"role": "assistant", "content": reply.get("reply"), "agent": reply.get("agent")},
        )
        return reply

    async def _handle_text(self, text: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        await self._sessions.append_history(
            payload["user_id"], {"role": "user", "content": text}
        )
        response = await self._crew.process_query(text, payload["user_id"], payload)
        await self._sessions.update_intent(payload["user_id"], response.get("agent", ""))
        return response

    async def _handle_voice(self, voice_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        transcript = await transcribe_audio(voice_url)
        if not transcript:
            response = {
                "agent": "voice_transcription",
                "reply": "I could not understand the audio. Could you type it instead?",
                "metadata": {"voice_url": voice_url},
            }
            await self._sessions.update_intent(payload["user_id"], response["agent"])
            return response

        await self._sessions.append_history(
            payload["user_id"],
            {
                "role": "user",
                "content": transcript,
                "metadata": {"voice_url": voice_url},
            },
        )
        response = await self._crew.process_query(transcript, payload["user_id"], payload)
        await self._sessions.update_intent(payload["user_id"], response.get("agent", ""))
        return response

    async def _handle_image(self, image_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = {
            "agent": "image_analysis",
            "reply": "Image messages are not yet supported. Please send text.",
            "metadata": {"image_url": image_url},
        }
        await self._sessions.update_intent(payload["user_id"], response["agent"])
        return response

    def _extract_reply(self, response: Dict[str, Any]) -> str:
        if "reply" in response:
            return str(response["reply"])
        if "response" in response and isinstance(response["response"], dict):
            return str(response["response"].get("message") or response["response"])
        return str(response.get("response") or "OK")

    async def get_session(self, user_id: str) -> SessionSnapshot:
        return await self._sessions.get_context(user_id)


__all__ = ["ConversationInterface", "IncomingMessage"]
