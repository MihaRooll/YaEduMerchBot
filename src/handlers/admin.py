import logging
import time
from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from ..auth import role_manager
from ..storage import storage

logger = logging.getLogger(__name__)

# Состояния пользователей для FSM
user_states = {}

def register_admin_handlers(bot, chat_manager):
    """Регистрирует обработчики админских команд"""
    
    @bot.message_handler(commands=['admin'])
    def handle_admin(message):
        """Обработчик команды /admin"""
        user_id = message.from_user.id
        
        if not role_manager.has_permission(user_id, "admin"):
            bot.reply_to(message, "❌ У вас нет прав администратора!")
            return
        
        # Отправляем новое сообщение для команды
        bot.send_message(
            chat_id=message.chat.id,
            text="🔐 <b>Админ-панель</b>\n\nВыберите раздел для управления:",
            reply_markup=get_admin_panel_keyboard(),
            parse_mode='HTML'
        )
    
    @bot.message_handler(commands=['adduser'])
    def handle_adduser(message):
        """Обработчик команды /adduser"""
        user_id = message.from_user.id
        
        if not role_manager.has_permission(user_id, "admin"):
            bot.reply_to(message, "❌ У вас нет прав администратора!")
            return
        
        # Инициализируем состояние пользователя
        user_states[user_id] = {
            'state': 'waiting_for_role',
            'data': {}
        }
        
        # Показываем форму выбора роли
        _show_role_selection_form(message.chat.id, chat_manager)
    
    @bot.message_handler(commands=['addchat'])
    def handle_addchat(message):
        """Обработчик команды /addchat - добавляет текущий чат в систему"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        logger.info(f"Попытка добавления чата {chat_id} пользователем {user_id}")
        
        # Проверяем права (админ или координатор)
        if not role_manager.has_permission(user_id, "admin") and not role_manager.has_permission(user_id, "coordinator"):
            bot.reply_to(message, "❌ У вас нет прав для добавления чатов!")
            return
        
        # Проверяем, не является ли это личным чатом
        if message.chat.type == "private":
            bot.reply_to(message, "❌ Команда /addchat работает только в групповых чатах!")
            return
        
        # Проверяем, не добавлен ли уже этот чат
        existing_chat = storage.get("chats.json", str(chat_id))
        if existing_chat:
            bot.reply_to(message, "✅ Этот чат уже добавлен в систему!")
            return
        
        # Генерируем уникальный индекс для чата
        all_chats = storage.get_all("chats.json")
        used_prefixes = set()
        
        # Собираем все используемые индексы
        for chat_info in all_chats.values():
            if chat_info.get('prefix'):
                used_prefixes.add(chat_info.get('prefix'))
        
        # Генерируем новый индекс
        new_prefix = None
        for i in range(26):  # A-Z
            candidate = chr(65 + i)  # ASCII: A=65, B=66, C=67...
            if candidate not in used_prefixes:
                new_prefix = candidate
                break
        
        # Если все латинские буквы заняты, используем цифры
        if not new_prefix:
            for i in range(10):  # 0-9
                candidate = str(i)
                if candidate not in used_prefixes:
                    new_prefix = candidate
                    break
        
        # Если и цифры заняты, используем комбинацию
        if not new_prefix:
            new_prefix = f"X{len(used_prefixes)}"
        
        # Добавляем чат в систему
        chat_data = {
            "chat_id": str(chat_id),
            "title": message.chat.title or "Без названия",
            "type": message.chat.type,
            "added_by": user_id,
            "added_at": str(int(time.time())),
            "is_active": True,
            "description": message.chat.description or "",
            "username": message.chat.username or "",
            "prefix": new_prefix
        }
        
        try:
            logger.info(f"Попытка сохранения чата: {chat_data}")
            storage.set("chats.json", str(chat_id), chat_data)
            logger.info(f"Чат успешно сохранен в storage")
            
            # Отправляем подтверждение
            bot.reply_to(message, f"✅ <b>Чат успешно добавлен в систему!</b>\n\n"
                                f"📝 <b>Название:</b> {chat_data['title']}\n"
                                f"🆔 <b>ID:</b> {chat_id}\n"
                                f"🔤 <b>Индекс:</b> {chat_data['prefix']}\n"
                                f"👤 <b>Добавил:</b> {user_id}\n"
                                f"📅 <b>Дата:</b> {time.strftime('%d.%m.%Y %H:%M')}\n\n"
                                f"Теперь бот может отправлять сообщения в этот чат.\n"
                                f"Заказы будут иметь номера вида: {chat_data['prefix']}-001, {chat_data['prefix']}-002...", 
                                parse_mode='HTML')
            
            # Логируем добавление
            logger.info(f"Чат {chat_id} ({chat_data['title']}) добавлен пользователем {user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении чата {chat_id}: {e}")
            bot.reply_to(message, f"❌ Ошибка при добавлении чата в систему!\n\nОшибка: {str(e)}")
    
    @bot.message_handler(func=lambda message: _is_waiting_for_id(message.from_user.id))
    def handle_user_id_input(message):
        """Обработчик ввода ID/username пользователя"""
        user_id = message.from_user.id
        
        if user_id not in user_states:
            return
        
        # Удаляем сообщение пользователя
        bot.delete_message(message.chat.id, message.message_id)
        
        user_input = message.text.strip()
        state_data = user_states[user_id]
        
        # Проверяем, что ввел пользователь
        if user_input.startswith('@'):
            # Это username
            username = user_input
            if len(username) < 3:
                # Показываем ошибку в сообщении чата
                content = f"➕ <b>Добавление пользователя</b>\n\n"
                content += f"Выбрана роль: <b>{state_data['data'].get('selected_role', 'Unknown')}</b>\n\n"
                content += "❌ <b>Неверный формат username!</b>\n\n"
                content += "Username должен содержать минимум 3 символа.\n\n"
                content += "📝 Введите ID пользователя или username:\n\n"
                content += "• <b>ID:</b> 123456789\n"
                content += "• <b>Username:</b> @username\n\n"
                content += "💡 Бот ждет ваше сообщение..."
                
                from ..keyboards import get_back_keyboard
                keyboard = get_back_keyboard("admin_manage_users")
                chat_manager.update_chat_message(message.chat.id, content, keyboard)
                return
            
            # Генерируем временный ID для username
            import hashlib
            temp_id = abs(hash(username)) % 1000000000
            state_data['data']['username'] = username  # Сохраняем username как строку
            state_data['data']['temp_id'] = temp_id
            
            # Показываем форму подтверждения
            _show_add_user_form_for_username(message.chat.id, chat_manager, temp_id, username)
            
        elif user_input.isdigit():
            # Это числовой ID
            target_user_id = int(user_input)
            if target_user_id < 100000000:
                # Показываем ошибку в сообщении чата
                content = f"➕ <b>Добавление пользователя</b>\n\n"
                content += f"Выбрана роль: <b>{state_data['data'].get('selected_role', 'Unknown')}</b>\n\n"
                content += "❌ <b>Неверный формат ID!</b>\n\n"
                content += "ID должен содержать минимум 9 цифр.\n\n"
                content += "📝 Введите ID пользователя или username:\n\n"
                content += "• <b>ID:</b> 123456789\n"
                content += "• <b>Username:</b> @username\n\n"
                content += "💡 Бот ждет ваше сообщение..."
                
                from ..keyboards import get_back_keyboard
                keyboard = get_back_keyboard("admin_manage_users")
                chat_manager.update_chat_message(message.chat.id, content, keyboard)
                return
            
            state_data['data']['target_user_id'] = target_user_id
            
            # Показываем форму подтверждения
            _show_add_user_form_for_id(message.chat.id, chat_manager, target_user_id)
            
        else:
            # Показываем ошибку в сообщении чата
            content = f"➕ <b>Добавление пользователя</b>\n\n"
            content += f"Выбрана роль: <b>{state_data['data'].get('selected_role', 'Unknown')}</b>\n\n"
            content += "❌ <b>Неверный формат!</b>\n\n"
            content += "Введите числовой ID или username (начинающийся с @)\n\n"
            content += "📝 Введите ID пользователя или username:\n\n"
            content += "• <b>ID:</b> 123456789\n"
            content += "• <b>Username:</b> @username\n\n"
            content += "💡 Бот ждет ваше сообщение..."
            
            from ..keyboards import get_back_keyboard
            keyboard = get_back_keyboard("admin_manage_users")
            chat_manager.update_chat_message(message.chat.id, content, keyboard)
            return
    
    @bot.message_handler(func=lambda message: _is_waiting_for_prefix(message.from_user.id))
    def handle_prefix_input(message):
        # Используем chat_manager из замыкания
        nonlocal chat_manager
        """Обработчик ввода нового индекса чата"""
        user_id = message.from_user.id
        
        if user_id not in user_states:
            return
        
        # Удаляем сообщение пользователя
        bot.delete_message(message.chat.id, message.message_id)
        
        user_input = message.text.strip()
        state_data = user_states[user_id]
        target_chat_id = state_data['data'].get('target_chat_id')
        
        if not target_chat_id:
            return
        
        # Проверяем, что ввел пользователь
        if len(user_input) < 1 or len(user_input) > 10:
            # Показываем ошибку в сообщении чата
            content = f"🔤 <b>Изменение индекса чата</b>\n\n"
            content += "❌ <b>Неверный формат индекса!</b>\n\n"
            content += "Индекс должен содержать от 1 до 10 символов.\n\n"
            content += "📝 Введите новый индекс:\n\n"
            content += "💡 <b>Примеры индексов:</b>\n"
            content += "• A, B, C, D... (латинские буквы)\n"
            content += "• А, Б, В, Г... (кириллица)\n"
            content += "• 1, 2, 3, 4... (цифры)\n"
            content += "• МСК, СПБ, ЕКБ... (сокращения)\n\n"
            content += "💡 Бот ждет ваше сообщение..."
            
            from ..keyboards import get_back_keyboard
            keyboard = get_back_keyboard("admin_settings")
            chat_manager.update_chat_message(message.chat.id, content, keyboard)
            return
        
        # Обрабатываем изменение индекса
        _handle_prefix_change(message.chat.id, user_id, target_chat_id, user_input, chat_manager)
        
        # Очищаем состояние
        del user_states[user_id]

def _is_waiting_for_id(user_id):
    """Проверяет, ждет ли бот ввода ID от пользователя"""
    return user_id in user_states and user_states[user_id]['state'] == 'waiting_for_id'

def _is_waiting_for_prefix(user_id):
    """Проверяет, ждет ли бот ввода индекса от пользователя"""
    return user_id in user_states and user_states[user_id]['state'] == 'waiting_for_prefix'

def _show_role_selection_form(chat_id, chat_manager):
    """Показывает форму выбора роли"""
    from ..keyboards import get_role_selection_keyboard
    
    content = "➕ <b>Добавление пользователя</b>\n\n"
    content += "Выберите роль для нового пользователя:"
    
    keyboard = get_role_selection_keyboard()
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_add_user_form_for_id(chat_id, chat_manager, target_user_id):
    """Показывает форму подтверждения для ID"""
    from ..keyboards import get_user_confirm_keyboard, get_back_keyboard
    
    # Нужно найти пользователя в состоянии по chat_id
    # Это временное решение - используем роль по умолчанию
    role = "admin"  # По умолчанию
    
    content = f"➕ <b>Добавление пользователя</b>\n\n"
    content += f"ID: <b>{target_user_id}</b>\n\n"
    content += "Подтвердите добавление пользователя:"
    
    keyboard = get_user_confirm_keyboard(str(target_user_id), role)
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_add_user_form_for_username(chat_id, chat_manager, temp_id, username):
    """Показывает форму подтверждения для username"""
    from ..keyboards import get_user_confirm_keyboard, get_back_keyboard
    
    # Нужно найти пользователя в состоянии по chat_id
    # Это временное решение - передаем chat_id как user_id
    role = "admin"  # По умолчанию
    
    content = f"➕ <b>Добавление пользователя</b>\n\n"
    content += f"Username: <b>{username}</b>\n"
    content += f"Временный ID: <b>{temp_id}</b>\n"
    content += "⚠️ Внимание: Это временный ID для username.\n\n"
    content += "Подтвердите добавление пользователя:"
    
    keyboard = get_user_confirm_keyboard(str(temp_id), role)
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_add_user_form(chat_id, chat_manager):
    """Показывает форму добавления пользователя"""
    from ..keyboards import get_role_selection_keyboard
    
    content = "➕ <b>Добавление пользователя</b>\n\n"
    content += "Выберите роль для нового пользователя:"
    
    keyboard = get_role_selection_keyboard()
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_users_list(chat_id, chat_manager):
    """Показывает список пользователей"""
    from ..keyboards import get_users_list_keyboard
    
    users = role_manager.get_all_active_users()
    
    if not users:
        content = "👥 <b>Список пользователей</b>\n\n"
        content += "Пользователи не найдены."
        keyboard = get_back_keyboard("admin_manage_users")
    else:
        content = "👥 <b>Список пользователей</b>\n\n"
        content += f"Найдено пользователей: {len(users)}\n\n"
        
        # Показываем первые 10 пользователей
        for i, user_data in enumerate(users[:10]):
            role_emoji = {"admin": "👑", "coordinator": "🧭", "promo": "🎤", "user": "👤"}.get(user_data.get('role', 'user'), '👤')
            content += f"{i+1}. {role_emoji} <b>{user_data.get('first_name', 'Unknown')}</b> (ID: {user_data.get('user_id')})\n"
            content += f"   Роль: {user_data.get('role', 'user')}\n\n"
        
        if len(users) > 10:
            content += f"... и еще {len(users) - 10} пользователей"
        
        keyboard = get_users_list_keyboard(users)
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_search_form(chat_id, chat_manager):
    """Показывает форму поиска пользователей"""
    from ..keyboards import get_back_keyboard
    
    content = "🔍 <b>Поиск пользователей</b>\n\n"
    content += "Функция поиска будет реализована в следующих версиях.\n\n"
    content += "Пока что используйте список пользователей."
    
    keyboard = get_back_keyboard("admin_manage_users")
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_user_statistics(chat_id, chat_manager):
    """Показывает статистику пользователей"""
    from ..keyboards import get_back_keyboard
    
    # Получаем всех пользователей и считаем статистику вручную
    users = role_manager.get_all_active_users()
    
    # Подсчитываем статистику
    total = len(users)
    admin_count = len([u for u in users if u.get('role') == 'admin'])
    coordinator_count = len([u for u in users if u.get('role') == 'coordinator'])
    promo_count = len([u for u in users if u.get('role') == 'promo'])
    user_count = len([u for u in users if u.get('role') == 'user'])
    blocked_count = len([u for u in users if u.get('blocked', False)])
    
    content = "📊 <b>Статистика пользователей</b>\n\n"
    content += f"👥 Всего пользователей: {total}\n"
    content += f"👑 Администраторы: {admin_count}\n"
    content += f"🧭 Координаторы: {coordinator_count}\n"
    content += f"🎤 Промо: {promo_count}\n"
    content += f"👤 Пользователи: {user_count}\n"
    content += f"🚫 Заблокированные: {blocked_count}\n"
    
    keyboard = get_back_keyboard("admin_manage_users")
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_block_user_list(chat_id, chat_manager):
    """Показывает список пользователей для блокировки"""
    from ..keyboards import get_back_keyboard
    
    # Получаем всех активных пользователей
    users = role_manager.get_all_active_users()
    
    if not users:
        content = "🚫 <b>Блокировка пользователей</b>\n\n"
        content += "Пользователи не найдены."
        keyboard = get_back_keyboard("admin_manage_users")
    else:
        # Фильтруем только незаблокированных пользователей
        active_users = [user for user in users if not user.get('blocked', False)]
        
        if not active_users:
            content = "🚫 <b>Блокировка пользователей</b>\n\n"
            content += "Все пользователи уже заблокированы."
            keyboard = get_back_keyboard("admin_manage_users")
        else:
            content = "🚫 <b>Блокировка пользователей</b>\n\n"
            content += f"Найдено активных пользователей: {len(active_users)}\n\n"
            content += "Выберите пользователя для блокировки:\n\n"
            
            # Показываем первые 10 пользователей
            for i, user_data in enumerate(active_users[:10]):
                role_emoji = {"admin": "👑", "coordinator": "🧭", "promo": "🎤", "user": "👤"}.get(user_data.get('role', 'user'), '👤')
                content += f"{i+1}. {role_emoji} <b>{user_data.get('first_name', 'Unknown')}</b> (ID: {user_data.get('user_id')})\n"
                content += f"   Роль: {user_data.get('role', 'user')}\n\n"
            
            if len(active_users) > 10:
                content += f"... и еще {len(active_users) - 10} пользователей"
            
            # Создаем клавиатуру со списком пользователей
            keyboard = _create_block_user_keyboard(active_users)
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _create_block_user_keyboard(users: list) -> InlineKeyboardMarkup:
    """Создает клавиатуру со списком пользователей для блокировки"""
    from ..keyboards import get_back_keyboard
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Добавляем кнопки для каждого пользователя (максимум 10)
    for i, user_data in enumerate(users[:10]):
        role_emoji = {"admin": "👑", "coordinator": "🧭", "promo": "🎤", "user": "👤"}.get(user_data.get('role', 'user'), '👤')
        name = user_data.get('first_name', 'Unknown')[:20]  # Ограничиваем длину
        user_id = user_data.get('user_id')
        
        keyboard.add(InlineKeyboardButton(
            f"{role_emoji} {name} (ID: {user_id})",
            callback_data=f"block_user_{user_id}"
        ))
    
    # Добавляем кнопку "Назад"
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_manage_users"))
    
    return keyboard

def _show_block_confirmation(chat_id, target_user_id, chat_manager):
    """Показывает подтверждение блокировки пользователя"""
    from ..keyboards import get_back_keyboard
    
    # Получаем данные пользователя
    user_data = storage.get("users.json", str(target_user_id))
    if not user_data:
        content = "❌ <b>Пользователь не найден!</b>"
        keyboard = get_back_keyboard("admin_block_user")
    else:
        content = f"🚫 <b>Подтверждение блокировки</b>\n\n"
        content += f"ID: <b>{target_user_id}</b>\n"
        content += f"Имя: <b>{user_data.get('first_name', 'Unknown')}</b>\n"
        content += f"Роль: <b>{user_data.get('role', 'user')}</b>\n\n"
        content += "Вы уверены, что хотите заблокировать этого пользователя?\n\n"
        content += "⚠️ <b>Внимание:</b> Заблокированный пользователь не сможет использовать бота."
        
        # Создаем клавиатуру подтверждения
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_block_{target_user_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data="admin_block_user"),
            InlineKeyboardButton("🔙 Назад", callback_data="admin_manage_users")
        )
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _create_unblock_user_keyboard(users: list) -> InlineKeyboardMarkup:
    """Создает клавиатуру со списком заблокированных пользователей для разблокировки"""
    from ..keyboards import get_back_keyboard
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Добавляем кнопки для каждого пользователя (максимум 10)
    for i, user_data in enumerate(users[:10]):
        role_emoji = {"admin": "👑", "coordinator": "🧭", "promo": "🎤", "user": "👤"}.get(user_data.get('role', 'user'), '👤')
        name = user_data.get('first_name', 'Unknown')[:20]  # Ограничиваем длину
        user_id = user_data.get('user_id')
        
        keyboard.add(InlineKeyboardButton(
            f"{role_emoji} {name} (ID: {user_id})",
            callback_data=f"unblock_user_{user_id}"
        ))
    
    # Добавляем кнопку "Назад"
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_manage_users"))
    
    return keyboard

def _show_unblock_user_list(chat_id, chat_manager):
    """Показывает список заблокированных пользователей"""
    from ..keyboards import get_back_keyboard
    
    # Получаем всех пользователей
    users = role_manager.get_all_active_users()
    
    if not users:
        content = "✅ <b>Разблокировка пользователей</b>\n\n"
        content += "Пользователи не найдены."
        keyboard = get_back_keyboard("admin_manage_users")
    else:
        # Фильтруем только заблокированных пользователей
        blocked_users = [user for user in users if user.get('blocked', False)]
        
        if not blocked_users:
            content = "✅ <b>Разблокировка пользователей</b>\n\n"
            content += "Нет заблокированных пользователей."
            keyboard = get_back_keyboard("admin_manage_users")
        else:
            content = "✅ <b>Разблокировка пользователей</b>\n\n"
            content += f"Найдено заблокированных пользователей: {len(blocked_users)}\n\n"
            content += "Выберите пользователя для разблокировки:\n\n"
            
            # Показываем первые 10 пользователей
            for i, user_data in enumerate(blocked_users[:10]):
                role_emoji = {"admin": "👑", "coordinator": "🧭", "promo": "🎤", "user": "👤"}.get(user_data.get('role', 'user'), '👤')
                content += f"{i+1}. {role_emoji} <b>{user_data.get('first_name', 'Unknown')}</b> (ID: {user_data.get('user_id')})\n"
                content += f"   Роль: {user_data.get('role', 'user')}\n\n"
            
            if len(blocked_users) > 10:
                content += f"... и еще {len(blocked_users) - 10} пользователей"
            
            # Создаем клавиатуру со списком пользователей
            keyboard = _create_unblock_user_keyboard(blocked_users)
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_change_role_list(chat_id, chat_manager):
    """Показывает список пользователей для изменения роли"""
    from ..keyboards import get_back_keyboard
    
    content = "🔄 <b>Изменение ролей</b>\n\n"
    content += "Функция изменения ролей будет реализована в следующих версиях.\n\n"
    content += "Пока что используйте основные функции управления."
    
    keyboard = get_back_keyboard("admin_manage_users")
    chat_manager.update_chat_message(chat_id, content, keyboard)

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
    
    content = "💬 <b>Список чатов</b>\n\n"
    if not chats:
        content += "📝 Чаты не найдены.\n\n"
        content += "Чтобы добавить чат:\n"
        content += "1. Добавьте бота в нужный чат\n"
        content += "2. Введите команду <code>/addchat</code> в чате"
    else:
        content += f"📊 Найдено чатов: {len(chats)}\n\n"
        
        # Сортируем чаты по дате добавления
        sorted_chats = sorted(chats.items(), 
                             key=lambda x: int(x[1].get('added_at', 0)), 
                             reverse=True)
        
        for i, (chat_id_from_data, chat_data) in enumerate(sorted_chats[:10], 1):
            # Получаем статус чата
            status = "✅ Активен" if chat_data.get('is_active', True) else "🚫 Неактивен"
            
            # Получаем тип чата с эмодзи
            chat_type = chat_data.get('type', 'unknown')
            type_emoji = {
                'group': '👥',
                'supergroup': '👥',
                'channel': '📢',
                'private': '👤'
            }.get(chat_type, '❓')
            
            # Получаем индекс чата
            prefix = chat_data.get('prefix', '❓')
            
            # Форматируем дату
            try:
                added_time = int(chat_data.get('added_at', 0))
                date_str = time.strftime('%d.%m.%Y %H:%M', time.localtime(added_time))
            except:
                date_str = "Неизвестно"
            
            content += f"{i}. {type_emoji} <b>{chat_data.get('title', 'Без названия')}</b>\n"
            content += f"   🆔 ID: {chat_id_from_data}\n"
            content += f"   🔤 Индекс: {prefix}\n"
            content += f"   📅 Добавлен: {date_str}\n"
            content += f"   📊 Статус: {status}\n"
            
            # Добавляем username если есть
            if chat_data.get('username'):
                content += f"   🔗 @{chat_data.get('username')}\n"
            
            content += "\n"
        
        if len(chats) > 10:
            content += f"... и еще {len(chats) - 10} чатов"
        
        # Создаем клавиатуру со списком чатов
        keyboard = _create_chats_list_keyboard(sorted_chats)
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _create_chats_list_keyboard(chats: list) -> InlineKeyboardMarkup:
    """Создает клавиатуру со списком чатов для управления"""
    from ..keyboards import get_back_keyboard
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Добавляем кнопки для каждого чата (максимум 10)
    for i, (chat_id_from_data, chat_data) in enumerate(chats[:10]):
        title = chat_data.get('title', 'Без названия')[:20]  # Ограничиваем длину
        status_emoji = "✅" if chat_data.get('is_active', True) else "🚫"
        prefix = chat_data.get('prefix', '❓')
        
        keyboard.add(InlineKeyboardButton(
            f"{status_emoji} [{prefix}] {title}",
            callback_data=f"chat_actions_{chat_id_from_data}"
        ))
    
    # Добавляем кнопку "Назад"
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_settings"))
    
    return keyboard

def _show_add_chat_form(chat_id, chat_manager):
    """Показывает форму добавления чата"""
    from ..keyboards import get_back_keyboard
    
    content = "➕ <b>Добавление чата</b>\n\n"
    content += "Чтобы добавить новый чат в систему:\n\n"
    content += "1️⃣ <b>Добавьте бота в нужный чат</b>\n"
    content += "2️⃣ <b>Сделайте бота администратором</b> (рекомендуется)\n"
    content += "3️⃣ <b>Введите команду</b> <code>/addchat</code> в чате\n\n"
    content += "⚠️ <b>Важно:</b>\n"
    content += "• Команда работает только в групповых чатах\n"
    content += "• Требуются права администратора или координатора\n"
    content += "• Бот должен быть участником чата\n\n"
    content += "📝 <b>После добавления:</b>\n"
    content += "• Чат появится в списке управляемых чатов\n"
    content += "• Бот сможет отправлять туда сообщения\n"
    content += "• Администраторы смогут управлять чатом"
    
    keyboard = get_back_keyboard("admin_manage_chats")
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_assign_coordinator_form(chat_id, chat_manager):
    """Показывает форму назначения координатора"""
    from ..keyboards import get_back_keyboard
    
    content = "🧭 <b>Назначение координатора</b>\n\n"
    content += "Функция назначения координаторов будет реализована в следующих версиях.\n\n"
    content += "Пока что используйте основные функции управления."
    
    keyboard = get_back_keyboard("admin_manage_chats")
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_chat_actions(chat_id, target_chat_id, chat_manager):
    """Показывает действия с чатом"""
    from ..keyboards import get_back_keyboard
    
    chat_data = storage.get("chats.json", str(target_chat_id))
    if not chat_data:
        content = "❌ <b>Чат не найден!</b>"
        keyboard = get_back_keyboard("admin_manage_chats")
    else:
        # Форматируем дату
        try:
            added_time = int(chat_data.get('added_at', 0))
            date_str = time.strftime('%d.%m.%Y %H:%M', time.localtime(added_time))
        except:
            date_str = "Неизвестно"
        
        # Получаем текущий индекс чата
        current_prefix = chat_data.get('prefix', 'Не задан')
        
        content = f"💬 <b>Управление чатом</b>\n\n"
        content += f"📝 <b>Название:</b> {chat_data.get('title', 'Без названия')}\n"
        content += f"🆔 <b>ID:</b> {target_chat_id}\n"
        content += f"🔤 <b>Индекс:</b> {current_prefix}\n"
        content += f"📅 <b>Добавлен:</b> {date_str}\n"
        content += f"👤 <b>Добавил:</b> {chat_data.get('added_by', 'Неизвестно')}\n"
        content += f"📊 <b>Статус:</b> {'✅ Активен' if chat_data.get('is_active', True) else '🚫 Неактивен'}\n"
        content += f"🔗 <b>Тип:</b> {chat_data.get('type', 'unknown')}\n\n"
        
        if chat_data.get('username'):
            content += f"🔗 <b>Username:</b> @{chat_data.get('username')}\n\n"
        
        if chat_data.get('description'):
            content += f"📄 <b>Описание:</b> {chat_data.get('description')}\n\n"
        
        content += "Выберите действие:"
        
        # Создаем клавиатуру с действиями
        from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        if chat_data.get('is_active', True):
            keyboard.add(InlineKeyboardButton("🚫 Деактивировать", callback_data=f"deactivate_chat_{target_chat_id}"))
        else:
            keyboard.add(InlineKeyboardButton("✅ Активировать", callback_data=f"activate_chat_{target_chat_id}"))
        
        keyboard.add(InlineKeyboardButton("🔤 Изменить индекс", callback_data=f"change_prefix_{target_chat_id}"))
        keyboard.add(InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_chat_{target_chat_id}"))
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_manage_chats"))
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_orders_management(chat_id, chat_manager):
    """Показывает управление заказами"""
    from ..keyboards import get_back_keyboard
    
    content = "📦 <b>Управление заказами</b>\n\n"
    content += "Функция управления заказами будет реализована в следующих версиях.\n\n"
    content += "Пока что используйте основные функции управления."
    
    keyboard = get_back_keyboard("admin_panel")
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_orders_list(chat_id, chat_manager):
    """Показывает список заказов"""
    from ..keyboards import get_back_keyboard
    
    content = "📋 <b>Список заказов</b>\n\n"
    content += "Функция просмотра заказов будет реализована в следующих версиях.\n\n"
    content += "Пока что используйте основные функции управления."
    
    keyboard = get_back_keyboard("admin_manage_orders")
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_orders_statistics(chat_id, chat_manager):
    """Показывает статистику заказов"""
    from ..keyboards import get_back_keyboard
    
    content = "📊 <b>Статистика заказов</b>\n\n"
    content += "Функция статистики заказов будет реализована в следующих версиях.\n\n"
    content += "Пока что используйте основные функции управления."
    
    keyboard = get_back_keyboard("admin_manage_orders")
    chat_manager.update_chat_message(chat_id, content, keyboard)

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
    for user_data in users.values():
        role = user_data.get('role', 'unknown')
        role_counts[role] = role_counts.get(role, 0) + 1
    
    content += "🔑 <b>По ролям:</b>\n"
    for role, count in role_counts.items():
        content += f"  {role}: {count}\n"
    
    keyboard = get_back_keyboard("admin_panel")
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _handle_add_role_selection(call, role, chat_manager):
    """Обрабатывает выбор роли для добавления пользователя"""
    from ..keyboards import get_back_keyboard
    
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    # Инициализируем состояние пользователя для добавления
    user_states[user_id] = {
        'state': 'waiting_for_id',
        'data': {'selected_role': role}
    }
    
    # Показываем форму ввода ID/username
    content = f"➕ <b>Добавление пользователя</b>\n\n"
    content += f"Выбрана роль: <b>{role}</b>\n\n"
    content += "📝 Введите ID пользователя или username:\n\n"
    content += "• <b>ID:</b> 123456789\n"
    content += "• <b>Username:</b> @username\n\n"
    content += "💡 Бот ждет ваше сообщение..."
    
    keyboard = get_back_keyboard("admin_manage_users")
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_input_form(chat_id, role, chat_manager):
    """Показывает форму ввода ID/username"""
    from ..keyboards import get_back_keyboard
    
    content = f"➕ <b>Добавление пользователя</b>\n\n"
    content += f"Выбрана роль: <b>{role}</b>\n\n"
    content += "📝 Введите ID пользователя или username:\n\n"
    content += "• <b>ID:</b> 123456789\n"
    content += "• <b>Username:</b> @username\n\n"
    content += "💡 Бот ждет ваше сообщение..."
    
    keyboard = get_back_keyboard("admin_manage_users")
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _handle_confirm_add_user(call, target_user_id, role, chat_manager):
    """Обрабатывает подтверждение добавления пользователя"""
    from ..keyboards import get_back_keyboard
    
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    # Получаем данные из состояния
    if user_id not in user_states:
        return
    
    state_data = user_states[user_id]
    username = state_data['data'].get('username')
    selected_role = state_data['data'].get('selected_role', role)
    
    # Добавляем пользователя
    if username and isinstance(username, str) and username.startswith('@'):
        # Для username используем временный ID
        success = role_manager.add_user(
            target_user_id, username, username, selected_role, user_id
        )
    else:
        # Для числового ID
        success = role_manager.add_user(
            target_user_id, f"User_{target_user_id}", "Unknown", selected_role, user_id
        )
    
    if success:
        content = "✅ <b>Пользователь успешно добавлен!</b>\n\n"
        content += f"ID: <b>{target_user_id}</b>\n"
        if username and isinstance(username, str) and username.startswith('@'):
            content += f"Username: <b>{username}</b>\n"
        content += f"Роль: <b>{selected_role}</b>\n\n"
        content += "Пользователь может теперь использовать бота."
    else:
        content = "❌ <b>Ошибка добавления пользователя!</b>\n\n"
        content += "Возможно, пользователь уже существует или произошла ошибка."
    
    # Очищаем состояние
    del user_states[user_id]
    
    keyboard = get_back_keyboard("admin_manage_users")
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_user_actions(chat_id, target_user_id, chat_manager):
    """Показывает действия с пользователем"""
    from ..keyboards import get_user_action_keyboard
    
    user_data = storage.get("users.json", str(target_user_id))
    if not user_data:
        content = "❌ <b>Пользователь не найден!</b>"
        keyboard = get_back_keyboard("admin_list_users")
    else:
        content = f"👤 <b>Управление пользователем</b>\n\n"
        content += f"ID: <b>{target_user_id}</b>\n"
        content += f"Имя: <b>{user_data.get('first_name', 'Unknown')}</b>\n"
        content += f"Роль: <b>{user_data.get('role', 'user')}</b>\n"
        content += f"Статус: <b>{'Активен' if not user_data.get('blocked', False) else 'Заблокирован'}</b>\n\n"
        content += "Выберите действие:"
        
        keyboard = get_user_action_keyboard(target_user_id)
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_role_change_form(chat_id, target_user_id, chat_manager):
    """Показывает форму изменения роли"""
    from ..keyboards import get_role_change_keyboard
    
    content = f"🔄 <b>Изменение роли пользователя</b>\n\n"
    content += f"ID: <b>{target_user_id}</b>\n\n"
    content += "Выберите новую роль:"
    
    keyboard = get_role_change_keyboard(target_user_id)
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _handle_role_change(chat_id, user_id, target_user_id, new_role, chat_manager):
    """Обрабатывает изменение роли пользователя"""
    from ..keyboards import get_back_keyboard
    
    success = role_manager.update_user_role(target_user_id, new_role, user_id)
    
    if success:
        content = "✅ <b>Роль пользователя изменена!</b>\n\n"
        content += f"ID: <b>{target_user_id}</b>\n"
        content += f"Новая роль: <b>{new_role}</b>"
    else:
        content = "❌ <b>Ошибка изменения роли!</b>\n\n"
        content += "Возможно, у вас недостаточно прав или произошла ошибка."
    
    keyboard = get_back_keyboard("admin_list_users")
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_block_confirmation(chat_id, target_user_id, chat_manager):
    """Показывает подтверждение блокировки"""
    from ..keyboards import get_block_confirm_keyboard
    
    user_data = storage.get("users.json", str(target_user_id))
    if not user_data:
        content = "❌ <b>Пользователь не найден!</b>"
        keyboard = get_back_keyboard("admin_list_users")
    else:
        content = f"🚫 <b>Подтверждение блокировки</b>\n\n"
        content += f"ID: <b>{target_user_id}</b>\n"
        content += f"Имя: <b>{user_data.get('first_name', 'Unknown')}</b>\n"
        content += f"Роль: <b>{user_data.get('role', 'user')}</b>\n\n"
        content += "Вы уверены, что хотите заблокировать этого пользователя?"
        
        keyboard = get_block_confirm_keyboard(target_user_id)
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _handle_user_block(chat_id, user_id, target_user_id, chat_manager):
    """Обрабатывает блокировку пользователя"""
    from ..keyboards import get_back_keyboard
    
    success = role_manager.block_user(target_user_id, user_id, "Заблокирован администратором")
    
    if success:
        content = "✅ <b>Пользователь заблокирован!</b>\n\n"
        content += f"ID: <b>{target_user_id}</b>\n"
        content += "Пользователь больше не может использовать бота."
    else:
        content = "❌ <b>Ошибка блокировки!</b>\n\n"
        content += "Возможно, у вас недостаточно прав или произошла ошибка."
    
    # Возвращаемся к списку блокировки
    keyboard = get_back_keyboard("admin_block_user")
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _handle_user_unblock(chat_id, user_id, target_user_id, chat_manager):
    """Обрабатывает разблокировку пользователя"""
    from ..keyboards import get_back_keyboard
    
    success = role_manager.unblock_user(target_user_id, user_id)
    
    if success:
        content = "✅ <b>Пользователь разблокирован!</b>\n\n"
        content += f"ID: <b>{target_user_id}</b>\n"
        content += "Пользователь снова может использовать бота."
    else:
        content = "❌ <b>Ошибка разблокировки!</b>\n\n"
        content += "Возможно, у вас недостаточно прав или произошла ошибка."
    
    # Возвращаемся к списку разблокировки
    keyboard = get_back_keyboard("admin_unblock_user")
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_users_list_page(chat_id, page, chat_manager):
    """Показывает страницу списка пользователей"""
    from ..keyboards import get_pagination_keyboard
    
    users = role_manager.get_all_active_users()
    
    if not users:
        content = "👥 <b>Список пользователей</b>\n\n"
        content += "Пользователи не найдены."
        keyboard = get_back_keyboard("admin_manage_users")
    else:
        # Пагинация
        per_page = 10
        total_pages = (len(users) + per_page - 1) // per_page
        
        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_users = users[start_idx:end_idx]
        
        content = f"👥 <b>Список пользователей</b>\n\n"
        content += f"Страница {page} из {total_pages}\n"
        content += f"Всего пользователей: {len(users)}\n\n"
        
        for i, user_data in enumerate(page_users, start_idx + 1):
            role_emoji = {"admin": "👑", "coordinator": "🧭", "promo": "🎤", "user": "👤"}.get(user_data.get('role', 'user'), '👤')
            content += f"{i}. {role_emoji} <b>{user_data.get('first_name', 'Unknown')}</b> (ID: {user_data.get('user_id')})\n"
            content += f"   Роль: {user_data.get('role', 'user')}\n\n"
        
        keyboard = get_pagination_keyboard(page, total_pages, "users_page_", "admin_manage_users")
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _handle_chat_deactivate(chat_id, user_id, target_chat_id, chat_manager):
    """Обрабатывает деактивацию чата"""
    from ..keyboards import get_back_keyboard
    
    chat_data = storage.get("chats.json", str(target_chat_id))
    if not chat_data:
        content = "❌ <b>Чат не найден!</b>"
        keyboard = get_back_keyboard("admin_manage_chats")
    else:
        # Деактивируем чат
        chat_data['is_active'] = False
        chat_data['deactivated_at'] = str(int(time.time()))
        chat_data['deactivated_by'] = user_id
        
        success = storage.set("chats.json", str(target_chat_id), chat_data)
        
        if success:
            content = "🚫 <b>Чат деактивирован!</b>\n\n"
            content += f"📝 <b>Название:</b> {chat_data.get('title', 'Без названия')}\n"
            content += f"🆔 <b>ID:</b> {target_chat_id}\n"
            content += f"📅 <b>Деактивирован:</b> {time.strftime('%d.%m.%Y %H:%M')}\n\n"
            content += "Чат больше не будет получать сообщения от бота."
            
            logger.info(f"Чат {target_chat_id} деактивирован пользователем {user_id}")
        else:
            content = "❌ <b>Ошибка деактивации чата!</b>"
        
        keyboard = get_back_keyboard("admin_manage_chats")
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _handle_chat_activate(chat_id, user_id, target_chat_id, chat_manager):
    """Обрабатывает активацию чата"""
    from ..keyboards import get_back_keyboard
    
    chat_data = storage.get("chats.json", str(target_chat_id))
    if not chat_data:
        content = "❌ <b>Чат не найден!</b>"
        keyboard = get_back_keyboard("admin_manage_chats")
    else:
        # Активируем чат
        chat_data['is_active'] = True
        chat_data['activated_at'] = str(int(time.time()))
        chat_data['activated_by'] = user_id
        
        # Удаляем поля деактивации
        chat_data.pop('deactivated_at', None)
        chat_data.pop('deactivated_by', None)
        
        success = storage.set("chats.json", str(target_chat_id), chat_data)
        
        if success:
            content = "✅ <b>Чат активирован!</b>\n\n"
            content += f"📝 <b>Название:</b> {chat_data.get('title', 'Без названия')}\n"
            content += f"🆔 <b>ID:</b> {target_chat_id}\n"
            content += f"📅 <b>Активирован:</b> {time.strftime('%d.%m.%Y %H:%M')}\n\n"
            content += "Чат снова будет получать сообщения от бота."
            
            logger.info(f"Чат {target_chat_id} активирован пользователем {user_id}")
        else:
            content = "❌ <b>Ошибка активации чата!</b>"
        
        keyboard = get_back_keyboard("admin_manage_chats")
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _handle_chat_delete(chat_id, user_id, target_chat_id, chat_manager):
    """Обрабатывает удаление чата"""
    from ..keyboards import get_back_keyboard
    
    chat_data = storage.get("chats.json", str(target_chat_id))
    if not chat_data:
        content = "❌ <b>Чат не найден!</b>"
        keyboard = get_back_keyboard("admin_manage_chats")
    else:
        # Удаляем чат
        success = storage.delete("chats.json", str(target_chat_id))
        
        if success:
            content = "🗑️ <b>Чат удален!</b>\n\n"
            content += f"📝 <b>Название:</b> {chat_data.get('title', 'Без названия')}\n"
            content += f"🆔 <b>ID:</b> {target_chat_id}\n"
            content += f"📅 <b>Удален:</b> {time.strftime('%d.%m.%Y %H:%M')}\n\n"
            content += "Чат больше не будет управляться ботом."
            
            logger.info(f"Чат {target_chat_id} удален пользователем {user_id}")
        else:
            content = "❌ <b>Ошибка удаления чата!</b>"
        
        keyboard = get_back_keyboard("admin_manage_chats")
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_change_prefix_form(chat_id, user_id, target_chat_id, chat_manager):
    """Показывает форму изменения индекса чата"""
    from ..keyboards import get_back_keyboard
    
    chat_data = storage.get("chats.json", str(target_chat_id))
    if not chat_data:
        content = "❌ <b>Чат не найден!</b>"
        keyboard = get_back_keyboard("admin_manage_chats")
    else:
        current_prefix = chat_data.get('prefix', 'Не задан')
        
        content = f"🔤 <b>Изменение индекса чата</b>\n\n"
        content += f"📝 <b>Название:</b> {chat_data.get('title', 'Без названия')}\n"
        content += f"🆔 <b>ID:</b> {target_chat_id}\n"
        content += f"🔤 <b>Текущий индекс:</b> {current_prefix}\n\n"
        content += "📝 <b>Введите новый индекс:</b>\n\n"
        content += "💡 <b>Примеры индексов:</b>\n"
        content += "• A, B, C, D... (латинские буквы)\n"
        content += "• А, Б, В, Г... (кириллица)\n"
        content += "• 1, 2, 3, 4... (цифры)\n"
        content += "• МСК, СПБ, ЕКБ... (сокращения)\n\n"
        content += "⚠️ <b>Важно:</b> Индекс будет использоваться в начале номера заказа.\n"
        content += "Например: A-001, B-002, C-003..."
        
        # Создаем клавиатуру с кнопкой "Назад"
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data=f"chat_actions_{target_chat_id}"))
        
        # Устанавливаем состояние ожидания ввода индекса
        user_states[user_id] = {
            'state': 'waiting_for_prefix',
            'data': {'target_chat_id': target_chat_id}
        }
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _handle_prefix_change(chat_id, user_id, target_chat_id, new_prefix, chat_manager):
    """Обрабатывает изменение индекса чата"""
    from ..keyboards import get_back_keyboard
    
    chat_data = storage.get("chats.json", str(target_chat_id))
    if not chat_data:
        content = "❌ <b>Чат не найден!</b>"
        keyboard = get_back_keyboard("admin_manage_chats")
    else:
        # Проверяем, не занят ли уже этот индекс другим чатом
        all_chats = storage.get_all("chats.json")
        prefix_conflict = False
        conflicting_chat = None
        
        for chat_id_key, chat_info in all_chats.items():
            if chat_id_key != str(target_chat_id) and chat_info.get('prefix') == new_prefix:
                prefix_conflict = True
                conflicting_chat = chat_info
                break
        
        if prefix_conflict:
            content = "❌ <b>Индекс уже занят!</b>\n\n"
            content += f"Индекс <b>{new_prefix}</b> уже используется чатом:\n"
            content += f"📝 <b>Название:</b> {conflicting_chat.get('title', 'Без названия')}\n"
            content += f"🆔 <b>ID:</b> {chat_id_key}\n\n"
            content += "Выберите другой индекс."
            
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data=f"change_prefix_{target_chat_id}"))
        else:
            # Обновляем индекс чата
            old_prefix = chat_data.get('prefix', 'Не задан')
            chat_data['prefix'] = new_prefix
            chat_data['prefix_changed_at'] = str(int(time.time()))
            chat_data['prefix_changed_by'] = user_id
            
            success = storage.set("chats.json", str(target_chat_id), chat_data)
            
            if success:
                content = "✅ <b>Индекс чата изменен!</b>\n\n"
                content += f"📝 <b>Название:</b> {chat_data.get('title', 'Без названия')}\n"
                content += f"🆔 <b>ID:</b> {target_chat_id}\n"
                content += f"🔤 <b>Старый индекс:</b> {old_prefix}\n"
                content += f"🔤 <b>Новый индекс:</b> {new_prefix}\n"
                content += f"📅 <b>Изменен:</b> {time.strftime('%d.%m.%Y %H:%M')}\n\n"
                content += f"Теперь заказы в этом чате будут иметь номера вида: {new_prefix}-001, {new_prefix}-002..."
                
                logger.info(f"Индекс чата {target_chat_id} изменен с '{old_prefix}' на '{new_prefix}' пользователем {user_id}")
            else:
                content = "❌ <b>Ошибка изменения индекса!</b>"
            
            keyboard = get_back_keyboard("admin_manage_chats")
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

# Импорты для клавиатур
def get_admin_panel_keyboard():
    """Возвращает клавиатуру админ-панели"""
    from ..keyboards import get_admin_panel_keyboard
    return get_admin_panel_keyboard()

def get_back_keyboard(callback_data):
    """Возвращает клавиатуру с кнопкой назад"""
    from ..keyboards import get_back_keyboard
    return get_back_keyboard(callback_data)
