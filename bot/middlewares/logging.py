"""Logging middleware."""

import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging user interactions."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process the event and log user interaction."""
        
        if isinstance(event, Message):
            user_id = event.from_user.id
            username = event.from_user.username or "No username"
            text = event.text or "No text"
            
            logger.info(
                f"Message from user {user_id} (@{username}): {text}"
            )
            
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            username = event.from_user.username or "No username"
            callback_data = event.data or "No data"
            
            logger.info(
                f"Callback from user {user_id} (@{username}): {callback_data}"
            )
        
        return await handler(event, data)
