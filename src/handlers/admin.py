import logging
from telebot import TeleBot
from telebot.types import Message, CallbackQuery
from ..auth import role_manager
from ..storage import storage

logger = logging.getLogger(__name__)

# Состояния пользователей для интерактивных команд
user_states = {}


def register_admin_handlers(bot: TeleBot, chat_manager):
    """Регистрация админских обработчиков"""
    
    @bot.message_handler(commands=['admin'])
    def handle_admin(message: Message):
        """Обработчик команды /admin"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if not role_manager.has_permission(user_id, "admin"):
            from ..keyboards import get_back_keyboard
            keyboard = get_back_keyboard("back_to_main")
            bot.send_message(
                chat_id=chat_id,
                text="❌ У вас нет прав администратора!",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            return
        
        # ОТПРАВЛЯЕМ НОВОЕ СООБЩЕНИЕ с админ-панелью
        from ..keyboards import get_admin_panel_keyboard
        
        admin_text = "🔐 <b>Админ-панель</b>\n\n"
        admin_text += f"👑 Администратор: <b>{message.from_user.first_name or 'Unknown'}</b>\n"
        admin_text += "Выберите раздел для управления:"
        
        keyboard = get_admin_panel_keyboard()
        
        bot.send_message(
            chat_id=chat_id,
            text=admin_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    @bot.message_handler(commands=['adduser'])
    def handle_add_user(message: Message):
        """Обработчик команды /adduser"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if not role_manager.has_permission(user_id, "admin"):
            from ..keyboards import get_back_keyboard
            keyboard = get_back_keyboard("back_to_main")
            chat_manager.update_chat_message(
                chat_id, 
                "❌ У вас нет прав администратора!", 
                keyboard
            )
            return
        
        # Показываем форму добавления пользователя
        _show_add_user_form(chat_id, chat_manager)
    
    @bot.message_handler(commands=['users'])
    def handle_list_users(message: Message):
        """Обработчик команды /users"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if not role_manager.has_permission(user_id, "admin"):
            from ..keyboards import get_back_keyboard
            keyboard = get_back_keyboard("back_to_main")
            chat_manager.update_chat_message(
                chat_id, 
                "❌ У вас нет прав администратора!", 
                keyboard
            )
            return
        
        # Показываем список пользователей
        _show_users_list(chat_id, chat_manager)
    
    @bot.message_handler(commands=['stats'])
    def handle_stats(message: Message):
        """Обработчик команды /stats"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if not role_manager.has_permission(user_id, "admin"):
            from ..keyboards import get_back_keyboard
            keyboard = get_back_keyboard("back_to_main")
            chat_manager.update_chat_message(
                chat_id, 
                "❌ У вас нет прав администратора!", 
                keyboard
            )
            return
        
        # Показываем статистику
        chat_manager.show_system_stats(chat_id, user_id)
    
    @bot.message_handler(func=lambda message: _is_waiting_for_id(message.from_user.id))
    def handle_user_id_input(message: Message):
        """Обработчик ввода ID/username пользователя"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        user_input = message.text.strip()
        
        # Удаляем сообщение пользователя
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        
        # Проверяем состояние пользователя
        if user_id not in user_states or user_states[user_id]['state'] != 'waiting_for_id':
            return
        
        # Валидация ввода
        target_user_id = None
        username = None
        
        if user_input.startswith('@'):
            # Это username
            username = user_input[1:]  # Убираем @
            if len(username) < 3:
                _show_invalid_input_message(chat_id, chat_manager, "Username слишком короткий")
                return
            # Генерируем временный ID для username
            target_user_id = abs(hash(username)) % 1000000000
        else:
            # Это должен быть числовой ID
            try:
                target_user_id = int(user_input)
                if target_user_id <= 0:
                    _show_invalid_input_message(chat_id, chat_manager, "ID должен быть положительным числом")
                    return
            except ValueError:
                _show_invalid_input_message(chat_id, chat_manager, "Неверный формат. Введите числовой ID или username")
                return
        
        # Сохраняем данные пользователя
        user_states[user_id]['target_user_id'] = target_user_id
        user_states[user_id]['username'] = username or "unknown"
        
        # Если роль уже выбрана, переходим к подтверждению
        if 'selected_role' in user_states[user_id]:
            role = user_states[user_id]['selected_role']
            _show_confirm_add_user(chat_id, chat_manager, target_user_id, username, role)
        else:
            # Показываем форму выбора роли
            if username:
                _show_add_user_form_for_username(chat_id, chat_manager, target_user_id, username)
            else:
                _show_add_user_form_for_id(chat_id, chat_manager, target_user_id)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
    def admin_callback_handler(call: CallbackQuery):
        """Обработчик админских callback-запросов"""
        bot.answer_callback_query(call.id)
        
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        
        # Проверяем права администратора
        if not role_manager.has_permission(user_id, "admin"):
            bot.answer_callback_query(call.id, "❌ Нет прав администратора!")
            return
        
        # Основная админ-панель
        if call.data == "admin_panel":
            from ..keyboards import get_admin_panel_keyboard
            content = "👑 <b>Панель администратора</b>\n\n"
            content += "Выберите раздел для управления:"
            keyboard = get_admin_panel_keyboard()
            chat_manager.update_chat_message(chat_id, content, keyboard)
        
        # Управление пользователями
        elif call.data == "admin_manage_users":
            from ..keyboards import get_user_management_keyboard
            content = "👥 <b>Управление пользователями</b>\n\n"
            content += "Выберите действие:"
            keyboard = get_user_management_keyboard()
            chat_manager.update_chat_message(chat_id, content, keyboard)
        elif call.data == "admin_add_user":
            _show_add_user_form(chat_id, chat_manager)
        elif call.data == "admin_list_users":
            _show_users_list(chat_id, chat_manager)
        elif call.data == "admin_search_users":
            _show_search_form(chat_id, chat_manager)
        elif call.data == "admin_user_stats":
            _show_user_statistics(chat_id, chat_manager)
        elif call.data == "admin_block_user":
            _show_block_user_list(chat_id, chat_manager)
        elif call.data == "admin_unblock_user":
            _show_unblock_user_list(chat_id, chat_manager)
        elif call.data == "admin_change_role":
            _show_change_role_list(chat_id, chat_manager)
        
        # Управление чатами
        elif call.data == "admin_manage_chats":
            _show_chat_management(chat_id, chat_manager)
        elif call.data == "admin_list_chats":
            _show_chats_list(chat_id, chat_manager)
        elif call.data == "admin_add_chat":
            _show_add_chat_form(chat_id, chat_manager)
        elif call.data == "admin_assign_coordinator":
            _show_assign_coordinator_form(chat_id, chat_manager)
        
        # Управление заказами
        elif call.data == "admin_manage_orders":
            _show_orders_management(chat_id, chat_manager)
        elif call.data == "admin_list_orders":
            _show_orders_list(chat_id, chat_manager)
        elif call.data == "admin_orders_stats":
            _show_orders_statistics(chat_id, chat_manager)
        
        # Системная статистика
        elif call.data == "admin_system_stats":
            _show_system_statistics(chat_id, chat_manager)
        
        # Обработка ролей и подтверждений
        elif call.data.startswith("add_role_"):
            role = call.data.replace("add_role_", "")
            _handle_add_role_selection(chat_id, user_id, role, chat_manager)
        elif call.data.startswith("confirm_add_"):
            parts = call.data.replace("confirm_add_", "").split("_")
            if len(parts) >= 2:
                target_user_id = int(parts[0])
                role = parts[1]
                _handle_confirm_add_user(chat_id, user_id, target_user_id, role, chat_manager)
        
        # Действия с пользователями
        elif call.data.startswith("user_actions_"):
            target_user_id = call.data.replace("user_actions_", "")
            _show_user_actions(chat_id, target_user_id, chat_manager)
        elif call.data.startswith("change_role_"):
            target_user_id = call.data.replace("change_role_", "")
            _show_role_change_form(chat_id, target_user_id, chat_manager)
        elif call.data.startswith("set_role_"):
            parts = call.data.replace("set_role_", "").split("_")
            if len(parts) >= 2:
                target_user_id = int(parts[0])
                new_role = parts[1]
                _handle_role_change(chat_id, user_id, target_user_id, new_role, chat_manager)
        elif call.data.startswith("block_user_"):
            target_user_id = call.data.replace("block_user_", "")
            _show_block_confirmation(chat_id, target_user_id, chat_manager)
        elif call.data.startswith("confirm_block_"):
            target_user_id = call.data.replace("confirm_block_", "")
            _handle_user_block(chat_id, user_id, int(target_user_id), chat_manager)
        elif call.data.startswith("unblock_user_"):
            target_user_id = call.data.replace("unblock_user_", "")
            _handle_user_unblock(chat_id, user_id, int(target_user_id), chat_manager)
        
        # Пагинация
        elif call.data.startswith("users_page_"):
            page = int(call.data.replace("users_page_", ""))
            _show_users_list_page(chat_id, page, chat_manager)


def _show_add_user_form(chat_id, chat_manager):
    """Показывает форму добавления пользователя"""
    from ..keyboards import get_role_selection_keyboard
    
    content = "➕ <b>Добавление пользователя</b>\n\n"
    content += "Выберите роль для нового пользователя:"
    
    keyboard = get_role_selection_keyboard()
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _show_add_user_form_for_id(chat_id, chat_manager, target_user_id):
    """Показывает форму с выбором роли для числового ID"""
    from ..keyboards import get_role_selection_keyboard
    
    content = f"➕ <b>Добавление пользователя</b>\n\n"
    content += f"ID пользователя: <code>{target_user_id}</code>\n\n"
    content += "Выберите роль для этого пользователя:"
    
    keyboard = get_role_selection_keyboard()
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _show_add_user_form_for_username(chat_id, chat_manager, target_user_id, username):
    """Показывает форму с выбором роли для username"""
    from ..keyboards import get_role_selection_keyboard
    
    content = f"➕ <b>Добавление пользователя</b>\n\n"
    content += f"Username: @{username}\n"
    content += f"Временный ID: {target_user_id}\n\n"
    content += "⚠️ <b>Внимание:</b> Это временный ID для username.\n"
    content += "Выберите роль для этого пользователя:"
    
    keyboard = get_role_selection_keyboard()
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _show_confirm_add_user(chat_id, chat_manager, target_user_id, username, role):
    """Показывает подтверждение добавления пользователя"""
    from ..keyboards import get_user_confirm_keyboard
    
    role_names = {
        "admin": "👑 Администратор",
        "coordinator": "🔧 Координатор", 
        "promo": "📢 Промо",
        "user": "👤 Пользователь"
    }
    
    content = f"✅ <b>Подтверждение добавления</b>\n\n"
    if username and username != "unknown":
        content += f"Username: @{username}\n"
        content += f"Временный ID: {target_user_id}\n"
    else:
        content += f"ID пользователя: <code>{target_user_id}</code>\n"
    content += f"Роль: {role_names.get(role, role)}\n\n"
    content += "Подтвердить добавление пользователя?"
    
    keyboard = get_user_confirm_keyboard(str(target_user_id), role)
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _show_invalid_input_message(chat_id, chat_manager, error_message):
    """Показывает сообщение об ошибке ввода"""
    from ..keyboards import get_back_keyboard
    
    content = f"❌ <b>Ошибка ввода</b>\n\n"
    content += f"{error_message}\n\n"
    content += "📝 <b>Введите ID пользователя:</b>\n\n"
    content += "Просто отправьте сообщение с ID пользователя или username.\n\n"
    content += "<b>Примеры:</b>\n"
    content += "123456789\n"
    content += "@username\n\n"
    content += "💡 Бот ждет ваше сообщение..."
    
    keyboard = get_back_keyboard("admin_manage_users")
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _show_users_list(chat_id, chat_manager):
    """Показывает список пользователей"""
    from ..keyboards import get_back_keyboard
    
    users = role_manager.get_all_active_users()
    
    if not users:
        content = "👥 <b>Список пользователей</b>\n\n"
        content += "Пользователей пока нет."
    else:
        content = f"👥 <b>Список пользователей ({len(users)})</b>\n\n"
        
        role_symbols = {
            "admin": "👑",
            "coordinator": "🔧", 
            "promo": "📢",
            "user": "👤"
        }
        
        for user in users:
            symbol = role_symbols.get(user["role"], "❓")
            content += f"{symbol} <b>{user['first_name']}</b>\n"
            content += f"   ID: <code>{user['user_id']}</code>\n"
            content += f"   Роль: {user['role']}\n"
            content += f"   Добавлен: {user.get('added_at', 'неизвестно')}\n\n"
    
    keyboard = get_back_keyboard("admin_manage_users")
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _handle_add_role_selection(chat_id, user_id, role, chat_manager):
    """Обработчик выбора роли для добавления пользователя"""
    role_names = {
        "admin": "👑 Администратор",
        "coordinator": "🔧 Координатор", 
        "promo": "📢 Промо",
        "user": "👤 Пользователь"
    }
    
    # Сохраняем выбранную роль в состоянии
    user_states[user_id] = {
        'state': 'waiting_for_id',
        'selected_role': role
    }
    
    content = f"➕ <b>Добавление {role_names.get(role, role)}</b>\n\n"
    content += f"Роль: {role_names.get(role, role)}\n\n"
    content += "📝 <b>Введите ID пользователя:</b>\n\n"
    content += "Просто отправьте сообщение с ID пользователя или username.\n\n"
    content += "<b>Примеры:</b>\n"
    content += "123456789\n"
    content += "@username\n\n"
    content += "💡 Бот ждет ваше сообщение..."
    
    from ..keyboards import get_back_keyboard
    keyboard = get_back_keyboard("admin_add_user")
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _handle_confirm_add_user(chat_id, user_id, target_user_id, role, chat_manager):
    """Обработчик подтверждения добавления пользователя"""
    try:
        # Получаем данные из состояния
        username = "unknown"
        if user_id in user_states and 'username' in user_states[user_id]:
            username = user_states[user_id]['username']
        
        # Добавляем пользователя
        success = role_manager.add_user(
            target_user_id, 
            username, 
            "New User", 
            role, 
            user_id
        )
        
        # Очищаем состояние
        if user_id in user_states:
            del user_states[user_id]
        
        if success:
            content = f"✅ <b>Пользователь добавлен!</b>\n\n"
            content += f"ID: <code>{target_user_id}</code>\n"
            if username != "unknown":
                content += f"Username: @{username}\n"
            content += f"Роль: {role}\n\n"
            content += "Пользователь успешно добавлен в систему."
        else:
            content = f"❌ <b>Ошибка добавления</b>\n\n"
            content += f"Не удалось добавить пользователя {target_user_id}.\n"
            content += "Возможно, пользователь уже существует."
        
        from ..keyboards import get_back_keyboard
        keyboard = get_back_keyboard("admin_manage_users")
        chat_manager.update_chat_message(chat_id, content, keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка добавления пользователя: {e}")
        content = "❌ <b>Произошла ошибка</b>\n\nПопробуйте еще раз."
        from ..keyboards import get_back_keyboard
        keyboard = get_back_keyboard("admin_manage_users")
        chat_manager.update_chat_message(chat_id, content, keyboard)


def _is_waiting_for_id(user_id: int) -> bool:
    """Проверяет, ждет ли пользователь ввода ID"""
    return (user_id in user_states and 
            user_states[user_id].get('state') == 'waiting_for_id')


# ===== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ =====

def _show_search_form(chat_id, chat_manager):
    """Показывает форму поиска пользователей"""
    from ..keyboards import get_back_keyboard
    
    content = "🔍 <b>Поиск пользователей</b>\n\n"
    content += "Введите запрос для поиска:\n"
    content += "• ID пользователя (например: 123456789)\n"
    content += "• Username (например: @username)\n"
    content += "• Имя пользователя\n\n"
    content += "💡 Просто отправьте сообщение с запросом..."
    
    keyboard = get_back_keyboard("admin_manage_users")
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _show_user_statistics(chat_id, chat_manager):
    """Показывает статистику пользователей"""
    from ..keyboards import get_back_keyboard
    
    stats = role_manager.get_user_stats()
    
    content = "📊 <b>Статистика пользователей</b>\n\n"
    content += f"👥 <b>Всего пользователей:</b> {stats['total_users']}\n"
    content += f"✅ <b>Активных:</b> {stats['active_users']}\n"
    content += f"🚫 <b>Заблокированных:</b> {stats['blocked_users']}\n\n"
    
    content += "🔑 <b>По ролям:</b>\n"
    for role, count in stats['by_role'].items():
        role_symbols = {"admin": "👑", "coordinator": "🔧", "promo": "📢", "user": "👤"}
        symbol = role_symbols.get(role, "❓")
        content += f"  {symbol} {role.capitalize()}: {count}\n"
    
    keyboard = get_back_keyboard("admin_manage_users")
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _show_block_user_list(chat_id, chat_manager):
    """Показывает список пользователей для блокировки"""
    from ..keyboards import get_user_list_keyboard, get_back_keyboard
    
    users = role_manager.get_all_active_users()
    # Исключаем заблокированных
    active_users = [u for u in users if not u.get('blocked', False)]
    
    if not active_users:
        content = "🚫 <b>Блокировка пользователей</b>\n\n"
        content += "Нет активных пользователей для блокировки."
        keyboard = get_back_keyboard("admin_manage_users")
        chat_manager.update_chat_message(chat_id, content, keyboard)
        return
    
    content = f"🚫 <b>Блокировка пользователей</b>\n\n"
    content += f"Выберите пользователя для блокировки ({len(active_users)} активных):"
    
    keyboard = get_user_list_keyboard(active_users)
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _show_unblock_user_list(chat_id, chat_manager):
    """Показывает список заблокированных пользователей"""
    from ..keyboards import get_user_list_keyboard, get_back_keyboard
    
    users = storage.get_all("users.json")
    blocked_users = []
    
    for user_id, user_data in users.items():
        if user_data.get('blocked', False):
            blocked_users.append({"user_id": user_id, **user_data})
    
    if not blocked_users:
        content = "✅ <b>Разблокировка пользователей</b>\n\n"
        content += "Нет заблокированных пользователей."
        keyboard = get_back_keyboard("admin_manage_users")
        chat_manager.update_chat_message(chat_id, content, keyboard)
        return
    
    content = f"✅ <b>Разблокировка пользователей</b>\n\n"
    content += f"Выберите пользователя для разблокировки ({len(blocked_users)} заблокированных):"
    
    keyboard = get_user_list_keyboard(blocked_users)
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _show_change_role_list(chat_id, chat_manager):
    """Показывает список пользователей для изменения роли"""
    from ..keyboards import get_user_list_keyboard
    
    users = role_manager.get_all_active_users()
    
    content = f"✏️ <b>Изменение ролей</b>\n\n"
    content += f"Выберите пользователя для изменения роли ({len(users)} пользователей):"
    
    keyboard = get_user_list_keyboard(users)
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _show_user_actions(chat_id, target_user_id, chat_manager):
    """Показывает действия с конкретным пользователем"""
    from ..keyboards import get_user_action_keyboard, get_back_keyboard
    
    user_data = storage.get("users.json", target_user_id)
    if not user_data:
        content = "❌ Пользователь не найден"
        keyboard = get_back_keyboard("admin_manage_users")
        chat_manager.update_chat_message(chat_id, content, keyboard)
        return
    
    role_symbols = {"admin": "👑", "coordinator": "🔧", "promo": "📢", "user": "👤"}
    symbol = role_symbols.get(user_data['role'], "❓")
    blocked_mark = " 🚫" if user_data.get('blocked', False) else ""
    
    content = f"👤 <b>Управление пользователем</b>\n\n"
    content += f"{symbol} <b>Имя:</b> {user_data['first_name']}{blocked_mark}\n"
    content += f"🆔 <b>ID:</b> <code>{target_user_id}</code>\n"
    content += f"👤 <b>Username:</b> @{user_data.get('username', 'не указан')}\n"
    content += f"🔑 <b>Роль:</b> {user_data['role']}\n"
    content += f"📅 <b>Добавлен:</b> {user_data.get('added_at', 'неизвестно')}\n"
    content += f"✅ <b>Активен:</b> {'Да' if user_data.get('is_active', False) else 'Нет'}\n"
    
    if user_data.get('blocked', False):
        content += f"🚫 <b>Заблокирован:</b> {user_data.get('blocked_at', 'неизвестно')}\n"
        if user_data.get('block_reason'):
            content += f"📝 <b>Причина:</b> {user_data['block_reason']}\n"
    
    keyboard = get_user_action_keyboard(target_user_id)
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _show_role_change_form(chat_id, target_user_id, chat_manager):
    """Показывает форму изменения роли"""
    from ..keyboards import get_role_change_keyboard, get_back_keyboard
    
    user_data = storage.get("users.json", target_user_id)
    if not user_data:
        content = "❌ Пользователь не найден"
        keyboard = get_back_keyboard("admin_manage_users")
        chat_manager.update_chat_message(chat_id, content, keyboard)
        return
    
    content = f"✏️ <b>Изменение роли</b>\n\n"
    content += f"👤 <b>Пользователь:</b> {user_data['first_name']}\n"
    content += f"🔑 <b>Текущая роль:</b> {user_data['role']}\n\n"
    content += "Выберите новую роль:"
    
    keyboard = get_role_change_keyboard(target_user_id)
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _handle_role_change(chat_id, admin_id, target_user_id, new_role, chat_manager):
    """Обрабатывает изменение роли пользователя"""
    from ..keyboards import get_back_keyboard
    
    success = role_manager.update_user_role(target_user_id, new_role, admin_id)
    
    if success:
        user_data = storage.get("users.json", str(target_user_id))
        content = f"✅ <b>Роль изменена!</b>\n\n"
        content += f"👤 <b>Пользователь:</b> {user_data['first_name']}\n"
        content += f"🔑 <b>Новая роль:</b> {new_role}\n\n"
        content += "Изменение успешно применено."
    else:
        content = f"❌ <b>Ошибка изменения роли</b>\n\n"
        content += "Не удалось изменить роль пользователя.\n"
        content += "Возможно, у вас недостаточно прав."
    
    keyboard = get_back_keyboard("admin_manage_users")
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _show_block_confirmation(chat_id, target_user_id, chat_manager):
    """Показывает подтверждение блокировки"""
    from ..keyboards import get_block_confirm_keyboard, get_back_keyboard
    
    user_data = storage.get("users.json", target_user_id)
    if not user_data:
        content = "❌ Пользователь не найден"
        keyboard = get_back_keyboard("admin_manage_users")
        chat_manager.update_chat_message(chat_id, content, keyboard)
        return
    
    content = f"🚫 <b>Подтверждение блокировки</b>\n\n"
    content += f"👤 <b>Пользователь:</b> {user_data['first_name']}\n"
    content += f"🆔 <b>ID:</b> <code>{target_user_id}</code>\n"
    content += f"🔑 <b>Роль:</b> {user_data['role']}\n\n"
    content += "⚠️ <b>Вы уверены, что хотите заблокировать этого пользователя?</b>\n\n"
    content += "Заблокированный пользователь потеряет доступ ко всем функциям бота."
    
    keyboard = get_block_confirm_keyboard(target_user_id)
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _handle_user_block(chat_id, admin_id, target_user_id, chat_manager):
    """Обрабатывает блокировку пользователя"""
    from ..keyboards import get_back_keyboard
    
    success = role_manager.block_user(target_user_id, admin_id, "Заблокирован администратором")
    
    if success:
        user_data = storage.get("users.json", str(target_user_id))
        content = f"🚫 <b>Пользователь заблокирован!</b>\n\n"
        content += f"👤 <b>Пользователь:</b> {user_data['first_name']}\n"
        content += f"🆔 <b>ID:</b> <code>{target_user_id}</code>\n\n"
        content += "Пользователь успешно заблокирован."
    else:
        content = f"❌ <b>Ошибка блокировки</b>\n\n"
        content += "Не удалось заблокировать пользователя."
    
    keyboard = get_back_keyboard("admin_manage_users")
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _handle_user_unblock(chat_id, admin_id, target_user_id, chat_manager):
    """Обрабатывает разблокировку пользователя"""
    from ..keyboards import get_back_keyboard
    
    success = role_manager.unblock_user(target_user_id, admin_id)
    
    if success:
        user_data = storage.get("users.json", str(target_user_id))
        content = f"✅ <b>Пользователь разблокирован!</b>\n\n"
        content += f"👤 <b>Пользователь:</b> {user_data['first_name']}\n"
        content += f"🆔 <b>ID:</b> <code>{target_user_id}</code>\n\n"
        content += "Пользователь успешно разблокирован."
    else:
        content = f"❌ <b>Ошибка разблокировки</b>\n\n"
        content += "Не удалось разблокировать пользователя."
    
    keyboard = get_back_keyboard("admin_manage_users")
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _show_users_list_page(chat_id, page, chat_manager):
    """Показывает страницу списка пользователей"""
    from ..keyboards import get_user_list_keyboard
    
    users = role_manager.get_all_active_users()
    
    content = f"👥 <b>Список пользователей</b>\n\n"
    content += f"Страница {page + 1}, всего пользователей: {len(users)}"
    
    keyboard = get_user_list_keyboard(users, page)
    chat_manager.update_chat_message(chat_id, content, keyboard)


# ===== УПРАВЛЕНИЕ ЧАТАМИ =====

def _show_chat_management(chat_id, chat_manager):
    """Показывает управление чатами"""
    from ..keyboards import get_chat_management_keyboard
    
    content = "💬 <b>Управление чатами</b>\n\n"
    content += "Выберите действие:"
    
    keyboard = get_chat_management_keyboard()
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _show_chats_list(chat_id, chat_manager):
    """Показывает список чатов"""
    from ..keyboards import get_back_keyboard
    
    chats = storage.get_all("chats.json")
    
    if not chats:
        content = "💬 <b>Список чатов</b>\n\n"
        content += "Чатов пока нет."
    else:
        content = f"💬 <b>Список чатов ({len(chats)})</b>\n\n"
        
        for chat_id_str, chat_data in chats.items():
            coordinator_id = chat_data.get('coordinator_id')
            coordinator_name = "не назначен"
            
            if coordinator_id:
                coordinator_data = storage.get("users.json", coordinator_id)
                if coordinator_data:
                    coordinator_name = coordinator_data.get('first_name', 'Unknown')
            
            content += f"💬 <b>{chat_data.get('title', 'Без названия')}</b>\n"
            content += f"   ID: <code>{chat_id_str}</code>\n"
            content += f"   Координатор: {coordinator_name}\n"
            content += f"   Префикс: {chat_data.get('prefix', 'не указан')}\n\n"
    
    keyboard = get_back_keyboard("admin_manage_chats")
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _show_add_chat_form(chat_id, chat_manager):
    """Показывает форму добавления чата"""
    from ..keyboards import get_back_keyboard
    
    content = "➕ <b>Добавление чата</b>\n\n"
    content += "Функция добавления чатов будет реализована в следующих версиях.\n\n"
    content += "Пока что чаты добавляются автоматически при инициализации данных."
    
    keyboard = get_back_keyboard("admin_manage_chats")
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _show_assign_coordinator_form(chat_id, chat_manager):
    """Показывает форму назначения координатора"""
    from ..keyboards import get_back_keyboard
    
    content = "🔧 <b>Назначение координаторов</b>\n\n"
    content += "Функция назначения координаторов будет реализована в следующих версиях.\n\n"
    content += "Используйте пока что изменение ролей пользователей."
    
    keyboard = get_back_keyboard("admin_manage_chats")
    chat_manager.update_chat_message(chat_id, content, keyboard)


# ===== УПРАВЛЕНИЕ ЗАКАЗАМИ =====

def _show_orders_management(chat_id, chat_manager):
    """Показывает управление заказами"""
    from ..keyboards import get_back_keyboard
    
    content = "📦 <b>Управление заказами</b>\n\n"
    content += "Функции управления заказами будут реализованы в следующих версиях:\n\n"
    content += "• Просмотр всех заказов\n"
    content += "• Фильтрация по статусу\n"
    content += "• Редактирование заказов\n"
    content += "• Назначение промо на заказы\n"
    content += "• Перенос между чатами"
    
    keyboard = get_back_keyboard("admin_panel")
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _show_orders_list(chat_id, chat_manager):
    """Показывает список заказов"""
    from ..keyboards import get_back_keyboard
    
    orders = storage.get_all("orders.json")
    
    content = f"📦 <b>Список заказов</b>\n\n"
    if not orders:
        content += "Заказов пока нет."
    else:
        content += f"Всего заказов: {len(orders)}\n\n"
        content += "Детальный просмотр заказов будет реализован в следующих версиях."
    
    keyboard = get_back_keyboard("admin_panel")
    chat_manager.update_chat_message(chat_id, content, keyboard)


def _show_orders_statistics(chat_id, chat_manager):
    """Показывает статистику заказов"""
    from ..keyboards import get_back_keyboard
    
    orders = storage.get_all("orders.json")
    
    content = "📊 <b>Статистика заказов</b>\n\n"
    content += f"📦 <b>Всего заказов:</b> {len(orders)}\n"
    content += f"🆕 <b>Новых:</b> 0\n"
    content += f"⚙️ <b>В работе:</b> 0\n"
    content += f"✅ <b>Выполненных:</b> 0\n\n"
    content += "Детальная статистика будет реализована в следующих версиях."
    
    keyboard = get_back_keyboard("admin_panel")
    chat_manager.update_chat_message(chat_id, content, keyboard)


# ===== СИСТЕМНАЯ СТАТИСТИКА =====

def _show_system_statistics(chat_id, chat_manager):
    """Показывает системную статистику"""
    from ..keyboards import get_back_keyboard
    
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
    active_users = 0
    blocked_users = 0
    
    for user_data in users.values():
        role = user_data.get('role', 'unknown')
        role_counts[role] = role_counts.get(role, 0) + 1
        
        if user_data.get('is_active', False):
            active_users += 1
        if user_data.get('blocked', False):
            blocked_users += 1
    
    content += "🔑 <b>По ролям:</b>\n"
    for role, count in role_counts.items():
        role_symbols = {"admin": "👑", "coordinator": "🔧", "promo": "📢", "user": "👤"}
        symbol = role_symbols.get(role, "❓")
        content += f"  {symbol} {role}: {count}\n"
    
    content += f"\n✅ <b>Активных пользователей:</b> {active_users}\n"
    content += f"🚫 <b>Заблокированных:</b> {blocked_users}"
    
    keyboard = get_back_keyboard("admin_panel")
    chat_manager.update_chat_message(chat_id, content, keyboard)