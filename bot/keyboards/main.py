"""Main keyboard layouts."""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Get main menu keyboard."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🛍️ Каталог"),
                KeyboardButton(text="📦 Мои заказы")
            ],
            [
                KeyboardButton(text="👤 Профиль"),
                KeyboardButton(text="📞 Поддержка")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard
