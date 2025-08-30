"""Catalog handlers."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.keyboards.catalog import get_catalog_keyboard, get_product_keyboard

router = Router()


@router.message(F.text == "🛍️ Каталог")
async def show_catalog(message: Message) -> None:
    """Show product catalog."""
    catalog_text = (
        "🛍️ <b>Каталог товаров</b>\n\n"
        "Выберите категорию товаров:"
    )
    
    await message.answer(
        catalog_text,
        reply_markup=get_catalog_keyboard()
    )


@router.callback_query(F.data.startswith("category_"))
async def show_category(callback: CallbackQuery) -> None:
    """Show products in category."""
    category_id = callback.data.split("_")[1]
    
    # TODO: Get products from database
    products_text = (
        f"📦 <b>Товары категории</b>\n\n"
        f"В данной категории пока нет товаров.\n"
        f"Следите за обновлениями!"
    )
    
    await callback.message.edit_text(
        products_text,
        reply_markup=get_catalog_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product_"))
async def show_product(callback: CallbackQuery) -> None:
    """Show product details."""
    product_id = callback.data.split("_")[1]
    
    # TODO: Get product from database
    product_text = (
        f"📦 <b>Товар #{product_id}</b>\n\n"
        f"📝 Описание: Описание товара\n"
        f"💰 Цена: 1000 ₽\n"
        f"📦 В наличии: 10 шт.\n"
    )
    
    await callback.message.edit_text(
        product_text,
        reply_markup=get_product_keyboard(product_id)
    )
    await callback.answer()
