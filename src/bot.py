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
        
        # Обработчики callback-запросов (один общий обработчик для всех)
        self.bot.callback_query_handler(func=lambda call: True)(self.handle_callback)
        
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
            
            # Логируем callback для отладки
            logger.info(f"Получен callback: {call.data} от пользователя {user_id} в чате {chat_id}")
            
            # Обрабатываем различные типы callback
            if call.data == "back_to_main":
                logger.info("Обрабатываем back_to_main")
                self._handle_back_to_main(call)
            elif call.data == "admin_panel":
                logger.info("Обрабатываем admin_panel")
                self.chat_manager.show_admin_panel(chat_id, user_id)
            elif call.data == "admin_users":
                logger.info("Обрабатываем admin_users")
                self.chat_manager.show_user_management(chat_id, user_id)
            elif call.data == "admin_stats":
                logger.info("Обрабатываем admin_stats")
                self.chat_manager.show_system_stats(chat_id, user_id)
            elif call.data == "admin_settings":
                logger.info("Обрабатываем admin_settings")
                self._handle_admin_settings(call)
            elif call.data == "admin_manage_chats":
                logger.info("Обрабатываем admin_manage_chats")
                self._handle_admin_manage_chats(call)
            elif call.data == "admin_system_settings":
                logger.info("Обрабатываем admin_system_settings")
                self._handle_admin_system_settings(call)
            elif call.data == "admin_logs":
                logger.info("Обрабатываем admin_logs")
                self._handle_admin_logs(call)
            elif call.data.startswith("coord_"):
                self._handle_coordinator_callback(call)
            elif call.data.startswith("promo_"):
                self._handle_promo_callback(call)
            elif call.data.startswith("user_"):
                self._handle_user_callback(call)
            elif call.data.startswith("chat_actions_"):
                logger.info("Обрабатываем chat_actions")
                target_chat_id = call.data.replace("chat_actions_", "")
                self._handle_chat_actions(call, target_chat_id)
            elif call.data.startswith("deactivate_chat_"):
                logger.info("Обрабатываем deactivate_chat")
                target_chat_id = call.data.replace("deactivate_chat_", "")
                self._handle_chat_deactivate(call, target_chat_id)
            elif call.data.startswith("activate_chat_"):
                logger.info("Обрабатываем activate_chat")
                target_chat_id = call.data.replace("activate_chat_", "")
                self._handle_chat_activate(call, target_chat_id)
            elif call.data.startswith("delete_chat_"):
                logger.info("Обрабатываем delete_chat")
                target_chat_id = call.data.replace("delete_chat_", "")
                self._handle_chat_delete(call, target_chat_id)
            elif call.data.startswith("change_prefix_"):
                logger.info("Обрабатываем change_prefix")
                target_chat_id = call.data.replace("change_prefix_", "")
                self._handle_change_prefix(call, target_chat_id)
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
        # Проверяем права администратора
        if not role_manager.has_permission(call.from_user.id, "admin"):
            logger.warning(f"Пользователь {call.from_user.id} не имеет прав администратора")
            self.bot.answer_callback_query(call.id, "❌ Нет прав администратора!")
            return
        
        # Обрабатываем различные админские callback'ы
        if call.data == "admin_manage_chats":
            self._handle_admin_manage_chats(call)
        elif call.data == "admin_system_settings":
            self._handle_admin_system_settings(call)
        elif call.data == "admin_logs":
            self._handle_admin_logs(call)
        else:
            logger.warning(f"Неизвестный админский callback: {call.data}")
            self.bot.answer_callback_query(call.id, "Неизвестная админская функция")
    
    def _handle_coordinator_callback(self, call: CallbackQuery):
        """Обработчик callback координатора"""
        from .keyboards import get_back_keyboard
        
        if call.data == "coord_add_promo":
            content = "📢 <b>Добавление промо-пользователей</b>\n\n"
            content += "Функция добавления промо будет реализована в следующих версиях.\n\n"
            content += "Пока что используйте админ-панель для управления пользователями."
        elif call.data == "coord_orders":
            content = "📦 <b>Управление заказами</b>\n\n"
            content += "Функция управления заказами будет реализована в следующих версиях."
        elif call.data == "coord_inventory":
            content = "📋 <b>Управление инвентарем</b>\n\n"
            content += "Функция управления инвентарем будет реализована в следующих версиях."
        else:
            content = "🔧 <b>Функция координатора</b>\n\n"
            content += "Эта функция будет реализована в следующих версиях."
        
        keyboard = get_back_keyboard("back_to_main")
        self.chat_manager.update_chat_message(call.message.chat.id, content, keyboard)
    
    def _handle_promo_callback(self, call: CallbackQuery):
        """Обработчик callback промо"""
        from .keyboards import get_back_keyboard
        
        if call.data == "promo_create_order":
            content = "📦 <b>Создание заказа</b>\n\n"
            content += "Функция создания заказов будет реализована в следующих версиях."
        elif call.data == "promo_my_orders":
            content = "📋 <b>Мои заказы</b>\n\n"
            content += "Функция просмотра заказов будет реализована в следующих версиях."
        elif call.data == "promo_stats":
            content = "📊 <b>Статистика промо</b>\n\n"
            content += "Функция статистики будет реализована в следующих версиях."
        else:
            content = "📢 <b>Функция промо</b>\n\n"
            content += "Эта функция будет реализована в следующих версиях."
        
        keyboard = get_back_keyboard("back_to_main")
        self.chat_manager.update_chat_message(call.message.chat.id, content, keyboard)
    
    def _handle_user_callback(self, call: CallbackQuery):
        """Обработчик callback пользователя"""
        from .keyboards import get_back_keyboard
        
        if call.data == "user_create_order":
            content = "📦 <b>Создание заказа</b>\n\n"
            content += "Функция создания заказов будет реализована в следующих версиях."
        elif call.data == "user_my_orders":
            content = "📋 <b>Мои заказы</b>\n\n"
            content += "Функция просмотра заказов будет реализована в следующих версиях."
        elif call.data == "user_help":
            content = "ℹ️ <b>Помощь</b>\n\n"
            content += "Для получения помощи обратитесь к администратору или координатору."
        else:
            content = "👤 <b>Функция пользователя</b>\n\n"
            content += "Эта функция будет реализована в следующих версиях."
        
        keyboard = get_back_keyboard("back_to_main")
        self.chat_manager.update_chat_message(call.message.chat.id, content, keyboard)
    
    def _handle_order_callback(self, call: CallbackQuery):
        """Обработчик callback заказов"""
        self.bot.answer_callback_query(call.id, "Функция заказа")
    
    def _handle_admin_settings(self, call: CallbackQuery):
        """Обработчик настроек администратора"""
        from .keyboards import get_admin_settings_keyboard
        
        content = "⚙️ <b>Настройки системы</b>\n\n"
        content += "Выберите раздел настроек для управления системой:"
        
        keyboard = get_admin_settings_keyboard()
        self.chat_manager.update_chat_message(call.message.chat.id, content, keyboard)
    
    def _handle_admin_manage_chats(self, call: CallbackQuery):
        """Обработчик управления чатами из меню настроек"""
        logger.info(f"Обрабатываем admin_manage_chats для пользователя {call.from_user.id}")
        from .handlers.admin import _show_chats_list
        _show_chats_list(call.message.chat.id, self.chat_manager)
    
    def _handle_admin_system_settings(self, call: CallbackQuery):
        """Обработчик системных настроек"""
        from .keyboards import get_back_keyboard
        
        content = "🔧 <b>Системные настройки</b>\n\n"
        content += "Функция системных настроек будет реализована в следующих версиях.\n\n"
        content += "Пока что используйте основные функции админ-панели."
        
        keyboard = get_back_keyboard("admin_settings")
        self.chat_manager.update_chat_message(call.message.chat.id, content, keyboard)
    
    def _handle_admin_logs(self, call: CallbackQuery):
        """Обработчик логов и мониторинга"""
        from .keyboards import get_back_keyboard
        
        content = "📊 <b>Логи и мониторинг</b>\n\n"
        content += "Функция просмотра логов будет реализована в следующих версиях.\n\n"
        content += "Пока что используйте основные функции админ-панели."
        
        keyboard = get_back_keyboard("admin_settings")
        self.chat_manager.update_chat_message(call.message.chat.id, content, keyboard)

    def _handle_chat_deactivate(self, call: CallbackQuery, target_chat_id: str):
        """Обработчик деактивации чата"""
        from .handlers.admin import _handle_chat_deactivate
        _handle_chat_deactivate(call.message.chat.id, call.from_user.id, target_chat_id, self.chat_manager)

    def _handle_chat_activate(self, call: CallbackQuery, target_chat_id: str):
        """Обработчик активации чата"""
        from .handlers.admin import _handle_chat_activate
        _handle_chat_activate(call.message.chat.id, call.from_user.id, target_chat_id, self.chat_manager)

    def _handle_chat_delete(self, call: CallbackQuery, target_chat_id: str):
        """Обработчик удаления чата"""
        from .handlers.admin import _handle_chat_delete
        _handle_chat_delete(call.message.chat.id, call.from_user.id, target_chat_id, self.chat_manager)

    def _handle_change_prefix(self, call: CallbackQuery, target_chat_id: str):
        """Обработчик изменения индекса чата"""
        from .handlers.admin import _show_change_prefix_form
        _show_change_prefix_form(call.message.chat.id, call.from_user.id, target_chat_id, self.chat_manager)

    def _handle_chat_actions(self, call: CallbackQuery, target_chat_id: str):
        """Обработчик действий с чатом"""
        from .handlers.admin import _show_chat_actions
        _show_chat_actions(call.message.chat.id, target_chat_id, self.chat_manager)

    def handle_unknown(self, message: Message):
        """Обработчик неизвестных команд"""
        from .handlers.admin import _is_waiting_for_id, _is_waiting_for_prefix
        
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Не показываем "неизвестная команда" если пользователь в интерактивном режиме
        if _is_waiting_for_id(user_id) or _is_waiting_for_prefix(user_id):
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
