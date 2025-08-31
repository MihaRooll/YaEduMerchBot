import logging
from telebot import TeleBot
from telebot.storage.memory_storage import StateMemoryStorage
from telebot.types import Message, CallbackQuery
from .handlers.admin import register_admin_handlers
from .auth import role_manager
from .chat_manager import ChatManager

logger = logging.getLogger(__name__)


class YaEduMerchBot:
    """Основной класс бота для мерча Я.Образования"""
    
    def __init__(self, token: str):
        self.bot = TeleBot(token, state_storage=StateMemoryStorage())
        self.chat_manager = ChatManager(self.bot)
        self._register_handlers()
        logger.info("Бот инициализирован")
    
    def _register_handlers(self):
        """Регистрация всех обработчиков"""
        # Базовые команды (регистрируем ПЕРВЫМИ)
        self.bot.message_handler(commands=['start'])(self.handle_start)
        self.bot.message_handler(commands=['help'])(self.handle_help)
        self.bot.message_handler(commands=['status'])(self.handle_status)
        self.bot.message_handler(commands=['menu'])(self.handle_menu)
        
        # Админские команды
        register_admin_handlers(self.bot, self.chat_manager)
        
        # Обработчики callback-запросов (исключаем админские - они обрабатываются в admin.py)
        self.bot.callback_query_handler(func=lambda call: not call.data.startswith('admin_'))(self.handle_callback)
        
        # Обработчик неизвестных команд (ПОСЛЕДНИМ)
        self.bot.message_handler(func=lambda message: True)(self.handle_unknown)
    
    def _check_project_readiness(self) -> bool:
        """Проверяет готовность проекта к работе"""
        try:
            # Проверяем наличие основных данных
            from .storage import storage
            users = storage.get_all("users.json")
            chats = storage.get_all("chats.json")
            inventory = storage.get_all("inventory.json")
            settings = storage.get_all("settings.json")
            
            # Проект считается готовым, если есть:
            # 1. Хотя бы один админ
            # 2. Хотя бы один чат
            # 3. Хотя бы один товар в инвентаре
            # 4. Базовые настройки
            
            has_admin = any(user.get('role') == 'admin' for user in users.values())
            has_chats = len(chats) > 0
            has_inventory = len(inventory) > 0
            has_settings = len(settings) > 0
            
            return has_admin and has_chats and has_inventory and has_settings
            
        except Exception as e:
            logger.error(f"Ошибка проверки готовности проекта: {e}")
            return False
    
    def _get_start_message(self, role: str, project_ready: bool) -> str:
        """Формирует стартовое сообщение в зависимости от роли и готовности проекта"""
        
        if not project_ready:
            # Проект не готов
            if role == "admin":
                return ("🔧 <b>Добро пожаловать, Администратор!</b>\n\n"
                       "❌ <b>Проект еще не настроен</b>\n\n"
                       "Для начала работы необходимо:\n"
                       "• Добавить координаторов и промо-пользователей\n"
                       "• Настроить чаты\n"
                       "• Добавить товары в инвентарь\n"
                       "• Настроить базовые параметры\n\n"
                       "Используйте /admin для настройки проекта")
            
            elif role == "coordinator":
                return ("🔧 <b>Добро пожаловать, Координатор!</b>\n\n"
                       "❌ <b>Проект еще не настроен</b>\n\n"
                       "Обратитесь к администратору для настройки:\n"
                       "• Чатов\n"
                       "• Инвентаря\n"
                       "• Базовых параметров\n\n"
                       "После настройки вы сможете создавать заказы")
            
            elif role == "promo":
                return ("📢 <b>Добро пожаловать, Промо-пользователь!</b>\n\n"
                       "❌ <b>Бот еще не принимает заказы</b>\n\n"
                       "Проект находится в настройке.\n"
                       "Обратитесь к координатору или администратору.\n\n"
                       "После настройки вы сможете помогать с оформлением заказов")
            
            else:  # user
                return ("👤 <b>Добро пожаловать!</b>\n\n"
                       "❌ <b>Бот еще не принимает заказы</b>\n\n"
                       "Проект находится в настройке.\n"
                       "Обратитесь к администратору.\n\n"
                       "После настройки вы сможете оформлять заказы")
        
        else:
            # Проект готов
            if role == "admin":
                return ("👑 <b>Добро пожаловать, Администратор!</b>\n\n"
                       "✅ <b>Проект готов к работе!</b>\n\n"
                       "Вы можете:\n"
                       "• Управлять пользователями\n"
                       "• Настраивать систему\n"
                       "• Просматривать статистику\n"
                       "• Создавать заказы\n\n"
                       "Используйте кнопки ниже для навигации")
            
            elif role == "coordinator":
                return ("🔧 <b>Добро пожаловать, Координатор!</b>\n\n"
                       "✅ <b>Проект готов к работе!</b>\n\n"
                       "Вы можете:\n"
                       "• Управлять промо-пользователями\n"
                       "• Настраивать инвентарь\n"
                       "• Создавать заказы\n\n"
                       "Используйте кнопки ниже для навигации")
            
            elif role == "promo":
                return ("📢 <b>Добро пожаловать, Промо-пользователь!</b>\n\n"
                       "✅ <b>Бот готов принимать заказы!</b>\n\n"
                       "Вы можете:\n"
                       "• Помогать с оформлением заказов\n"
                       "• Работать с клиентами\n\n"
                       "Используйте кнопки ниже для навигации")
            
            else:  # user
                return ("👤 <b>Добро пожаловать!</b>\n\n"
                       "✅ <b>Бот готов принимать заказы!</b>\n\n"
                       "Вы можете:\n"
                       "• Просматривать каталог\n"
                       "• Оформлять заказы\n"
                       "• Выбирать размеры и цвета\n\n"
                       "Используйте кнопки ниже для навигации")

    def handle_start(self, message: Message):
        """Обработчик команды /start"""
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"
        first_name = message.from_user.first_name or "Unknown"
        chat_id = message.chat.id
        
        # Получаем роль пользователя
        role = role_manager.get_user_role(user_id)
        
        # Если пользователь новый, добавляем его
        if not role_manager.get_user_data(user_id):
            role_manager.add_user(user_id, username, first_name, "user", user_id)
            role = "user"
        
        # Проверяем готовность проекта
        project_ready = self._check_project_readiness()
        
        # Формируем приветственное сообщение
        start_text = self._get_start_message(role, project_ready)
        
        # ОТПРАВЛЯЕМ НОВОЕ СООБЩЕНИЕ (не редактируем существующее)
        from .keyboards import get_main_menu_keyboard, get_back_keyboard
        
        if project_ready:
            keyboard = get_main_menu_keyboard(role)
        else:
            keyboard = get_back_keyboard("back_to_main")
        
        # Отправляем новое сообщение
        self.bot.send_message(
            chat_id=chat_id,
            text=start_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    def handle_help(self, message: Message):
        """Обработчик команды /help"""
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        help_text = "📚 <b>Справка по командам:</b>\n\n"
        help_text += "🔐 <b>Админские команды:</b>\n"
        help_text += "/admin - Админская панель\n"
        help_text += "/adduser - Добавить пользователя\n"
        help_text += "/users - Список пользователей\n"
        help_text += "/stats - Статистика системы\n\n"
        help_text += "📋 <b>Общие команды:</b>\n"
        help_text += "/start - Начать работу\n"
        help_text += "/menu - Главное меню\n"
        help_text += "/help - Эта справка\n"
        help_text += "/status - Ваш статус\n\n"
        help_text += "💡 <b>Примечание:</b> Используйте кнопки для навигации"
        
        # ОТПРАВЛЯЕМ НОВОЕ СООБЩЕНИЕ
        from .keyboards import get_back_keyboard
        keyboard = get_back_keyboard("back_to_main")
        
        self.bot.send_message(
            chat_id=chat_id,
            text=help_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    def handle_status(self, message: Message):
        """Обработчик команды /status"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        user_data = role_manager.get_user_data(user_id)
        
        if not user_data:
            status_text = "❌ Пользователь не найден в системе"
            from .keyboards import get_back_keyboard
            keyboard = get_back_keyboard("back_to_main")
            self.bot.send_message(
                chat_id=chat_id,
                text=status_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            return
        
        status_text = "📊 <b>Ваш статус:</b>\n\n"
        status_text += f"👤 <b>Имя:</b> {user_data['first_name']}\n"
        status_text += f"🔑 <b>Роль:</b> {user_data['role']}\n"
        status_text += f"📅 <b>Добавлен:</b> {user_data['added_at']}\n"
        status_text += f"✅ <b>Активен:</b> {'Да' if user_data['is_active'] else 'Нет'}\n"
        
        if user_data['role'] == 'admin':
            status_text += "\n👑 <b>Права:</b> Полный доступ ко всем функциям"
        elif user_data['role'] == 'coordinator':
            status_text += "\n🔧 <b>Права:</b> Можете добавлять промо-пользователей"
        elif user_data['role'] == 'promo':
            status_text += "\n📢 <b>Права:</b> Можете работать с заказами"
        else:
            status_text += "\n👤 <b>Права:</b> Базовые права пользователя"
        
        # ОТПРАВЛЯЕМ НОВОЕ СООБЩЕНИЕ
        from .keyboards import get_back_keyboard
        keyboard = get_back_keyboard("back_to_main")
        
        self.bot.send_message(
            chat_id=chat_id,
            text=status_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    def handle_menu(self, message: Message):
        """Обработчик команды /menu - показывает главное меню"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        role = role_manager.get_user_role(user_id)
        
        # ОТПРАВЛЯЕМ НОВОЕ СООБЩЕНИЕ с главным меню
        from .keyboards import get_main_menu_keyboard
        
        menu_text = "🏠 <b>Главное меню</b>\n\n"
        menu_text += f"👤 Пользователь: <b>{message.from_user.first_name or 'Unknown'}</b>\n"
        menu_text += f"🔑 Роль: <b>{role}</b>\n\n"
        menu_text += "Выберите нужный раздел:"
        
        keyboard = get_main_menu_keyboard(role)
        
        self.bot.send_message(
            chat_id=chat_id,
            text=menu_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    def handle_callback(self, call: CallbackQuery):
        """Обработчик всех callback-запросов"""
        try:
            # Отвечаем на callback
            self.bot.answer_callback_query(call.id)
            
            chat_id = call.message.chat.id
            user_id = call.from_user.id
            
            # Обрабатываем различные типы callback
            if call.data == "back_to_main":
                self._handle_back_to_main(call)
            elif call.data.startswith("coord_"):
                self._handle_coordinator_callback(call)
            elif call.data.startswith("promo_"):
                self._handle_promo_callback(call)
            elif call.data.startswith("user_"):
                self._handle_user_callback(call)
            elif call.data.startswith("order_"):
                self._handle_order_callback(call)
            else:
                self.bot.answer_callback_query(call.id, "Неизвестная команда")
                
        except Exception as e:
            logger.error(f"Ошибка обработки callback {call.data}: {e}")
            self.bot.answer_callback_query(call.id, "Произошла ошибка")
    
    def _handle_back_to_main(self, call: CallbackQuery):
        """Обработчик возврата в главное меню"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        role = role_manager.get_user_role(user_id)
        
        # Показываем главное меню
        self.chat_manager.show_main_menu(chat_id, user_id, role)
    
    def _handle_admin_callback(self, call: CallbackQuery):
        """Обработчик админских callback"""
        # Пока просто отвечаем
        self.bot.answer_callback_query(call.id, "Админская функция")
    
    def _handle_coordinator_callback(self, call: CallbackQuery):
        """Обработчик callback координатора"""
        self.bot.answer_callback_query(call.id, "Функция координатора")
    
    def _handle_promo_callback(self, call: CallbackQuery):
        """Обработчик callback промо"""
        self.bot.answer_callback_query(call.id, "Функция промо")
    
    def _handle_user_callback(self, call: CallbackQuery):
        """Обработчик callback пользователя"""
        self.bot.answer_callback_query(call.id, "Функция пользователя")
    
    def _handle_order_callback(self, call: CallbackQuery):
        """Обработчик callback заказов"""
        self.bot.answer_callback_query(call.id, "Функция заказа")
    
    def handle_unknown(self, message: Message):
        """Обработчик неизвестных команд"""
        from .handlers.admin import _is_waiting_for_id
        
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Не показываем "неизвестная команда" если пользователь в интерактивном режиме
        if _is_waiting_for_id(user_id):
            return
        
        unknown_text = "❓ Неизвестная команда\n\n"
        unknown_text += "Используйте /help для получения справки\n"
        unknown_text += "Или /menu для возврата в главное меню"
        
        # Кнопка возврата к главному меню
        from .keyboards import get_back_keyboard
        keyboard = get_back_keyboard("back_to_main")
        
        self.chat_manager.update_chat_message(chat_id, unknown_text, keyboard)
    
    def run(self):
        """Запуск бота"""
        logger.info("Запуск бота...")
        try:
            self.bot.polling(none_stop=True)
        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем")
        except Exception as e:
            logger.error(f"Ошибка работы бота: {e}")
            raise
