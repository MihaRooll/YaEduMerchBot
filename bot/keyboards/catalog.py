"""Catalog keyboard layouts."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_catalog_keyboard() -> InlineKeyboardMarkup:
    """Get catalog categories keyboard."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📚 Учебные материалы",
                    callback_data="category_books"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎒 Аксессуары",
                    callback_data="category_accessories"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👕 Одежда",
                    callback_data="category_clothing"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Сувениры",
                    callback_data="category_souvenirs"
                )
            ]
        ]
    )
    return keyboard


def get_product_keyboard(product_id: str) -> InlineKeyboardMarkup:
    """Get product actions keyboard."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 Добавить в корзину",
                    callback_data=f"add_to_cart_{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Купить сейчас",
                    callback_data=f"buy_now_{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к каталогу",
                    callback_data="back_to_catalog"
                )
            ]
        ]
    )
    return keyboard
