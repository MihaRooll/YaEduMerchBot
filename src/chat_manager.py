import logging
from typing import Dict, Optional, Any
from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup
from .storage import storage
from .keyboards import get_main_menu_keyboard, get_admin_panel_keyboard

logger = logging.getLogger(__name__)


class ChatManager:
    """Менеджер чатов - одно сообщение на чат, которое постоянно редактируется"""
    
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self._chat_messages: Dict[str, Dict[str, Any]] = {}  # chat_id -> message_info
        # Загружаем существующие сообщения из БД
        self._load_existing_messages()
    
    def get_or_create_chat_message(self, chat_id: int, user_id: int, 
                                  role: str) -> Dict[str, Any]:
        """
        Получает существующее сообщение чата или создает новое
        Возвращает информацию о сообщении
        """
        chat_key = str(chat_id)
        
        if chat_key in self._chat_messages:
            return self._chat_messages[chat_key]
        
        # Создаем новое сообщение для чата
        message_info = self._create_chat_message(chat_id, user_id, role)
        self._chat_messages[chat_key] = message_info
        
        # Сохраняем в БД
        self._save_chat_message(chat_id, message_info)
        
        return message_info
    
    def _create_chat_message(self, chat_id: int, user_id: int, role: str) -> Dict[str, Any]:
        """Создает новое сообщение для чата"""
        # Формируем содержимое в зависимости от роли
        if role == "admin":
            content = self._get_admin_content(user_id)
            keyboard = get_admin_panel_keyboard()
        else:
            content = self._get_user_content(user_id, role)
            keyboard = get_main_menu_keyboard(role)
        
        # Отправляем сообщение
        sent_message = self.bot.send_message(
            chat_id=chat_id,
            text=content,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return {
            'message_id': sent_message.message_id,
            'chat_id': chat_id,
            'user_id': user_id,
            'role': role,
            'content': content,
            'created_at': 'now'
        }
    
    def update_chat_message(self, chat_id: int, new_content: str, 
                           new_keyboard: InlineKeyboardMarkup) -> bool:
        """
        Обновляет существующее сообщение чата
        """
        chat_key = str(chat_id)
        
        if chat_key not in self._chat_messages:
            logger.warning(f"Сообщение для чата {chat_id} не найдено")
            return False
        
        message_info = self._chat_messages[chat_key]
        
        try:
            # Редактируем существующее сообщение
            self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_info['message_id'],
                text=new_content,
                reply_markup=new_keyboard,
                parse_mode='HTML'
            )
            
            # Обновляем кеш
            message_info['content'] = new_content
            
            # Обновляем в БД
            self._update_chat_message(chat_id, message_info)
            
            logger.info(f"Сообщение чата {chat_id} обновлено")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления сообщения чата {chat_id}: {e}")
            return False
    
    def show_main_menu(self, chat_id: int, user_id: int, role: str) -> bool:
        """Показывает главное меню в чате"""
        content = self._get_user_content(user_id, role)
        keyboard = get_main_menu_keyboard(role)
        
        return self.update_chat_message(chat_id, content, keyboard)
    
    def show_admin_panel(self, chat_id: int, user_id: int) -> bool:
        """Показывает админ-панель в чате"""
        content = self._get_admin_content(user_id)
        keyboard = get_admin_panel_keyboard()
        
        return self.update_chat_message(chat_id, content, keyboard)
    
    def show_user_management(self, chat_id: int, user_id: int) -> bool:
        """Показывает управление пользователями в чате"""
        from .keyboards import get_user_management_keyboard, get_back_keyboard
        
        content = "👥 <b>Управление пользователями</b>\n\nВыберите действие:"
        keyboard = get_user_management_keyboard()
        
        return self.update_chat_message(chat_id, content, keyboard)
    
    def show_chat_management(self, chat_id: int, user_id: int) -> bool:
        """Показывает управление чатами в чате"""
        from .keyboards import get_chat_management_keyboard
        
        content = "💬 <b>Управление чатами</b>\n\nВыберите действие:"
        keyboard = get_chat_management_keyboard()
        
        return self.update_chat_message(chat_id, content, keyboard)
    
    def show_inventory_management(self, chat_id: int, user_id: int) -> bool:
        """Показывает управление инвентарем в чате"""
        from .keyboards import get_inventory_management_keyboard
        
        content = "📦 <b>Управление инвентарем</b>\n\nВыберите действие:"
        keyboard = get_inventory_management_keyboard()
        
        return self.update_chat_message(chat_id, content, keyboard)
    
    def show_system_stats(self, chat_id: int, user_id: int) -> bool:
        """Показывает системную статистику в чате"""
        from .keyboards import get_back_keyboard
        
        # Получаем статистику
        users = storage.get_all("users.json")
        chats = storage.get_all("chats.json")
        orders = storage.get_all("orders.json")
        inventory = storage.get_all("inventory.json")
        
        content = "📊 <b>Системная статистика:</b>\n\n"
        content += f"👥 <b>Пользователи:</b> {len(users)}\n"
        content += f"💬 <b>Чаты:</b> {len(chats)}\n"
        content += f"📦 <b>Заказы:</b> {len(orders)}\n"
        content += f"📋 <b>Товары в инвентаре:</b> {len(inventory)}\n\n"
        
        # Статистика по ролям
        role_counts = {}
        for user_data in users.values():
            role = user_data.get('role', 'unknown')
            role_counts[role] = role_counts.get(role, 0) + 1
        
        content += "🔑 <b>По ролям:</b>\n"
        for role, count in role_counts.items():
            content += f"  {role}: {count}\n"
        
        keyboard = get_back_keyboard("admin_panel")
        
        return self.update_chat_message(chat_id, content, keyboard)
    
    def _get_admin_content(self, user_id: int) -> str:
        """Формирует содержимое для админа"""
        user_data = storage.get("users.json", str(user_id))
        
        content = "🔐 <b>Админ-панель</b>\n\n"
        content += f"👑 Администратор: <b>{user_data.get('first_name', 'Unknown')}</b>\n"
        content += "Выберите раздел для управления:"
        
        return content
    
    def _get_user_content(self, user_id: int, role: str) -> str:
        """Формирует содержимое для пользователя"""
        user_data = storage.get("users.json", str(user_id))
        
        content = "🏠 <b>Главное меню</b>\n\n"
        content += f"👤 Пользователь: <b>{user_data.get('first_name', 'Unknown')}</b>\n"
        content += f"🔑 Роль: <b>{role}</b>\n\n"
        content += "Выберите нужный раздел:"
        
        return content
    
    def _save_chat_message(self, chat_id: int, message_info: Dict[str, Any]):
        """Сохраняет информацию о сообщении чата в БД"""
        # Создаем копию без keyboard (он не сериализуется в JSON)
        save_info = message_info.copy()
        if 'keyboard' in save_info:
            del save_info['keyboard']
        storage.set("chat_messages.json", str(chat_id), save_info)
    
    def _update_chat_message(self, chat_id: int, message_info: Dict[str, Any]):
        """Обновляет информацию о сообщении чата в БД"""
        # Создаем копию без keyboard (он не сериализуется в JSON)
        save_info = message_info.copy()
        if 'keyboard' in save_info:
            del save_info['keyboard']
        storage.set("chat_messages.json", str(chat_id), save_info)
    
    def get_chat_message_info(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Получает информацию о сообщении чата"""
        chat_key = str(chat_id)
        return self._chat_messages.get(chat_key)
    
    def _load_existing_messages(self):
        """Загружает существующие сообщения из БД в кеш"""
        try:
            existing_messages = storage.get_all("chat_messages.json")
            for chat_id, message_info in existing_messages.items():
                self._chat_messages[chat_id] = message_info
            logger.info(f"Загружено {len(existing_messages)} существующих сообщений чатов")
        except Exception as e:
            logger.warning(f"Не удалось загрузить существующие сообщения: {e}")
    
    def clear_chat_cache(self, chat_id: int = None):
        """Очищает кеш сообщений чата"""
        if chat_id:
            chat_key = str(chat_id)
            if chat_key in self._chat_messages:
                del self._chat_messages[chat_key]
                logger.info(f"Кеш чата {chat_id} очищен")
        else:
            self._chat_messages.clear()
            logger.info("Весь кеш чатов очищен")