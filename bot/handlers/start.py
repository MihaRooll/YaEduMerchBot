"""Start command handler."""

from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards.main import get_main_keyboard

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """Handle /start command."""
    welcome_text = (
        "🎓 <b>Добро пожаловать в YaEduMerchBot!</b>\n\n"
        "Здесь вы можете:\n"
        "🛍️ Просмотреть каталог товаров\n"
        "📦 Оформить заказ\n"
        "👤 Управлять профилем\n"
        "📞 Получить поддержку\n\n"
        "Выберите действие из меню ниже:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard()
    )
