"""Handlers package initialization."""

from aiogram import Dispatcher

from .start import router as start_router
from .admin import router as admin_router
from .catalog import router as catalog_router


def setup_handlers(dp: Dispatcher) -> None:
    """Setup all handlers for the bot."""
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(catalog_router)
