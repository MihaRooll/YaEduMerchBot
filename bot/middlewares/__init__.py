"""Middlewares package initialization."""

from aiogram import Dispatcher

from .logging import LoggingMiddleware


def setup_middlewares(dp: Dispatcher) -> None:
    """Setup all middlewares for the bot."""
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
