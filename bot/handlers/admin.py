"""Admin handlers."""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message

from config.settings import Settings

router = Router()
settings = Settings()


@router.message(Command("admin"))
async def admin_panel(message: Message) -> None:
    """Handle /admin command."""
    if message.from_user.id not in settings.get_admin_ids():
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    admin_text = (
        "🔧 <b>Панель администратора</b>\n\n"
        "Доступные команды:\n"
        "📊 /stats - Статистика бота\n"
        "👥 /users - Список пользователей\n"
        "📦 /orders - Управление заказами\n"
        "🛍️ /products - Управление товарами\n"
    )
    
    await message.answer(admin_text)


@router.message(Command("stats"))
async def bot_stats(message: Message) -> None:
    """Show bot statistics."""
    if message.from_user.id not in settings.get_admin_ids():
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    # TODO: Implement actual statistics
    stats_text = (
        "📊 <b>Статистика бота</b>\n\n"
        "👥 Пользователей: 0\n"
        "📦 Заказов: 0\n"
        "🛍️ Товаров: 0\n"
        "💰 Общая сумма: 0 ₽\n"
    )
    
    await message.answer(stats_text)
