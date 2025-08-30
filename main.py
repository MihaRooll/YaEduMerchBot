"""
YaEduMerchBot - Telegram bot for Yandex Educational Merchandise
Main entry point for the bot application.
"""

import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from bot.handlers import setup_handlers
from bot.middlewares import setup_middlewares
from config.settings import Settings


async def main():
    """Main function to start the bot."""
    # Load environment variables
    load_dotenv()
    
    # Initialize settings
    settings = Settings()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize bot and dispatcher
    bot_token = settings.get_bot_token()
    if not bot_token:
        logging.error("Bot token not found! Please set BOT_TOKEN or TG_TOKEN environment variable.")
        return
    
    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Setup middlewares and handlers
    setup_middlewares(dp)
    setup_handlers(dp)
    
    # Start polling
    logging.info("Starting YaEduMerchBot...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
