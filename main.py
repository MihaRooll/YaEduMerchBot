from telebot import TeleBot
from telebot.storage import StateMemoryStorage

import config
import db
from handlers.start import register_handlers


def main() -> None:
    db.init_db()
    bot = TeleBot(config.TELEGRAM_TOKEN, state_storage=StateMemoryStorage())
    register_handlers(bot)
    bot.infinity_polling()


if __name__ == "__main__":
    main()
