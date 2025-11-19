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
from app.strands.conversation import ConversationInterface, IncomingMessage
from app.strands.context_store import SessionStore
from app.crew.crew import get_crew

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env", override=False)


class TelegramJennyBot:
    """Adapter that pipes Telegram updates into the Jenny conversation interface."""

    def __init__(self, token: str) -> None:
        self.token = token
        self.session_store = SessionStore()
        self.crew = get_crew()
        self.conversation = ConversationInterface(self.crew, self.session_store)
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
            f"Hi {name}! I’m Jenny. Tell me something to remember or ask a question."
        )

    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.message.text:
            return
        user_id = str(update.effective_user.id)
        message = IncomingMessage(user_id=user_id, text=update.message.text)
        reply = await self.conversation.handle_message(message)
        await update.message.reply_text(reply.get("reply", ""))

    async def _handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.message.voice:
            return
        file = await context.bot.get_file(update.message.voice.file_id)
        voice_url = file.file_path
        message = IncomingMessage(
            user_id=str(update.effective_user.id),
            voice_url=voice_url,
            metadata={"telegram": {"voice_duration": update.message.voice.duration}},
        )
        reply = await self.conversation.handle_message(message)
        await update.message.reply_text(reply.get("reply", "I processed the audio."))

    async def _handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.message.photo:
            return
        file = await context.bot.get_file(update.message.photo[-1].file_id)
        image_url = file.file_path
        message = IncomingMessage(
            user_id=str(update.effective_user.id),
            image_url=image_url,
            metadata={"telegram": {"caption": update.message.caption}},
        )
        reply = await self.conversation.handle_message(message)
        await update.message.reply_text(reply.get("reply", "I received the image."))

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
