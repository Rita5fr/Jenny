"""Telegram bot interface for Jenny."""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.core.db import init_pool
from app.services.voice import transcribe_audio
from app.crew.crew import get_crew

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env", override=False)


class TelegramJennyBot:
    """Telegram bot that connects directly to CrewAI orchestrator."""

    def __init__(self, token: str) -> None:
        self.token = token
        self.crew = get_crew()
        init_pool()
        self.application = Application.builder().token(self.token).build()
        self._register_handlers()

    def _register_handlers(self) -> None:
        self.application.add_handler(CommandHandler("start", self._start))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text)
        )
        self.application.add_handler(
            MessageHandler(filters.VOICE | filters.AUDIO, self._handle_voice)
        )
        self.application.add_handler(
            MessageHandler(filters.PHOTO, self._handle_photo)
        )

    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_user:
            name = update.effective_user.first_name or update.effective_user.username
        else:
            name = "there"
        await update.message.reply_text(
            f"Hi {name}! I'm Jenny. Tell me something to remember or ask a question."
        )

    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.message.text:
            return

        user_id = str(update.effective_user.id)
        text = update.message.text

        # Process with CrewAI directly - it will use Mem0 for context
        response = await self.crew.process_query(
            query=text,
            user_id=user_id,
            context={"user_id": user_id}
        )

        await update.message.reply_text(response.get("reply", "I processed your message."))

    async def _handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.message.voice:
            return

        user_id = str(update.effective_user.id)
        file = await context.bot.get_file(update.message.voice.file_id)
        voice_url = file.file_path

        # Transcribe audio
        transcript = await transcribe_audio(voice_url)

        if not transcript:
            await update.message.reply_text(
                "I could not understand the audio. Could you type it instead?"
            )
            return

        # Process with CrewAI directly - it will use Mem0 for context
        response = await self.crew.process_query(
            query=transcript,
            user_id=user_id,
            context={"user_id": user_id, "voice_url": voice_url}
        )

        await update.message.reply_text(response.get("reply", "I processed the audio."))

    async def _handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.message.photo:
            return

        # Image processing not yet implemented
        await update.message.reply_text(
            "Image messages are not yet supported. Please send text or voice messages."
        )

    def run(self) -> None:
        logger.info("Starting Telegram bot polling.")
        self.application.run_polling(close_loop=False)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is required.")
    bot = TelegramJennyBot(token)
    bot.run()


if __name__ == "__main__":
    main()
