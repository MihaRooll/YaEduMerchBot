from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any


def get_main_menu_keyboard(user_role: str) -> InlineKeyboardMarkup:
    """Главное меню в зависимости от роли пользователя"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    if user_role == "admin":
        keyboard.add(
            InlineKeyboardButton("🔐 Админ-панель", callback_data="admin_panel"),
            InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
            InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings")
        )
    elif user_role == "coordinator":
        keyboard.add(
            InlineKeyboardButton("📢 Добавить промо", callback_data="coord_add_promo"),
            InlineKeyboardButton("📦 Управление заказами", callback_data="coord_orders"),
            InlineKeyboardButton("📋 Инвентарь", callback_data="coord_inventory")
        )
    elif user_role == "promo":
        keyboard.add(
            InlineKeyboardButton("📦 Создать заказ", callback_data="promo_create_order"),
            InlineKeyboardButton("📋 Мои заказы", callback_data="promo_my_orders"),
            InlineKeyboardButton("📊 Статистика", callback_data="promo_stats")
        )
    else:  # user
        keyboard.add(
            InlineKeyboardButton("📦 Создать заказ", callback_data="user_create_order"),
            InlineKeyboardButton("📋 Мои заказы", callback_data="user_my_orders"),
            InlineKeyboardButton("ℹ️ Помощь", callback_data="user_help")
        )
    
    return keyboard


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура админ-панели"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("👥 Управление пользователями", callback_data="admin_manage_users"),
        InlineKeyboardButton("💬 Управление чатами", callback_data="admin_manage_chats"),
        InlineKeyboardButton("📦 Управление инвентарем", callback_data="admin_manage_inventory"),
        InlineKeyboardButton("📊 Системная статистика", callback_data="admin_system_stats"),
        InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
    )
    return keyboard


def get_user_management_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления пользователями"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Добавить пользователя", callback_data="admin_add_user"),
        InlineKeyboardButton("🔍 Поиск пользователей", callback_data="admin_search_users"),
        InlineKeyboardButton("✏️ Изменить роль", callback_data="admin_change_role"),
        InlineKeyboardButton("🚫 Заблокировать", callback_data="admin_block_user"),
        InlineKeyboardButton("✅ Разблокировать", callback_data="admin_unblock_user"),
        InlineKeyboardButton("📋 Список всех", callback_data="admin_list_users"),
        InlineKeyboardButton("📊 Статистика", callback_data="admin_user_stats"),
        InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")
    )
    return keyboard


def get_chat_management_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления чатами"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Добавить чат", callback_data="admin_add_chat"),
        InlineKeyboardButton("📋 Список чатов", callback_data="admin_list_chats"),
        InlineKeyboardButton("🔧 Назначить координатора", callback_data="admin_assign_coordinator"),
        InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")
    )
    return keyboard


def get_inventory_management_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления инвентарем"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Добавить товар", callback_data="admin_add_item"),
        InlineKeyboardButton("✏️ Изменить количество", callback_data="admin_edit_quantity"),
        InlineKeyboardButton("📋 Список товаров", callback_data="admin_list_items"),
        InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")
    )
    return keyboard


def get_order_creation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура создания заказа"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📏 Выбрать размер", callback_data="order_select_size"),
        InlineKeyboardButton("🎨 Выбрать цвет", callback_data="order_select_color"),
        InlineKeyboardButton("📷 Загрузить фото", callback_data="order_upload_photo"),
        InlineKeyboardButton("💬 Выбрать чаты", callback_data="order_select_chats"),
        InlineKeyboardButton("✅ Подтвердить заказ", callback_data="order_confirm"),
        InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
    )
    return keyboard


def get_size_selection_keyboard(sizes: List[str]) -> InlineKeyboardMarkup:
    """Клавиатура выбора размера"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    # Добавляем кнопки размеров
    size_buttons = []
    for size in sizes:
        size_buttons.append(InlineKeyboardButton(size, callback_data=f"size_{size}"))
    
    # Группируем по 3 в ряд
    for i in range(0, len(size_buttons), 3):
        row = size_buttons[i:i+3]
        keyboard.add(*row)
    
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="order_back_to_start"))
    return keyboard


def get_color_selection_keyboard(colors: List[str], selected_size: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора цвета"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    # Добавляем кнопки цветов
    color_buttons = []
    for color in colors:
        color_buttons.append(InlineKeyboardButton(color, callback_data=f"color_{color}_{selected_size}"))
    
    # Группируем по 3 в ряд
    for i in range(0, len(color_buttons), 3):
        row = color_buttons[i:i+3]
        keyboard.add(*row)
    
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="order_back_to_start"))
    return keyboard


def get_chat_selection_keyboard(chats: List[Dict[str, Any]], selected_chats: List[str]) -> InlineKeyboardMarkup:
    """Клавиатура выбора чатов"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for chat in chats:
        chat_id = str(chat["chat_id"])
        is_selected = chat_id in selected_chats
        status = "✅" if is_selected else "❌"
        
        keyboard.add(InlineKeyboardButton(
            f"{status} {chat['title']} ({chat['prefix']})",
            callback_data=f"chat_toggle_{chat_id}"
        ))
    
    keyboard.add(
        InlineKeyboardButton("✅ Готово", callback_data="chats_selected"),
        InlineKeyboardButton("🔙 Назад", callback_data="order_back_to_start")
    )
    return keyboard


def get_order_confirmation_keyboard(order_data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения заказа"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Подтвердить", callback_data="order_final_confirm"),
        InlineKeyboardButton("✏️ Изменить размер", callback_data="order_change_size"),
        InlineKeyboardButton("🖼 Изменить фото", callback_data="order_change_photo"),
        InlineKeyboardButton("💬 Изменить чаты", callback_data="order_change_chats"),
        InlineKeyboardButton("🔙 Назад", callback_data="order_back_to_start")
    )
    return keyboard

def get_order_review_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура предпросмотра заказа для FSM"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🔁 Сменить размер", callback_data="order_change_size"),
        InlineKeyboardButton("🖼 Сменить изображение", callback_data="order_change_photo"),
        InlineKeyboardButton("➡️ Выбрать чаты", callback_data="order_select_chats"),
        InlineKeyboardButton("🔙 Назад", callback_data="order_back_to_start")
    )
    return keyboard


def get_operator_keyboard(order_id: str, status: str) -> InlineKeyboardMarkup:
    """Клавиатура для операторов"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    if status == "sent":
        keyboard.add(
            InlineKeyboardButton("🖨 Печать", callback_data=f"operator_print_{order_id}"),
            InlineKeyboardButton("✅ Готово", callback_data=f"operator_done_{order_id}")
        )
    elif status == "printed":
        keyboard.add(
            InlineKeyboardButton("✅ Готово", callback_data=f"operator_done_{order_id}")
        )
    elif status == "done":
        keyboard.add(
            InlineKeyboardButton("📋 Завершен", callback_data="order_completed")
        )
    
    return keyboard


def get_back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """Универсальная кнопка "Назад" """
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data=callback_data))
    return keyboard


def get_admin_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек администратора"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("💬 Управление чатами", callback_data="admin_manage_chats"),
        InlineKeyboardButton("🔧 Системные настройки", callback_data="admin_system_settings"),
        InlineKeyboardButton("📊 Логи и мониторинг", callback_data="admin_logs"),
        InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")
    )
    return keyboard


def get_role_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора роли для добавления пользователя"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("👑 Администратор", callback_data="add_role_admin"),
        InlineKeyboardButton("🔧 Координатор", callback_data="add_role_coordinator"),
        InlineKeyboardButton("📢 Промо", callback_data="add_role_promo"),
        InlineKeyboardButton("👤 Пользователь", callback_data="add_role_user"),
        InlineKeyboardButton("🔙 Назад", callback_data="admin_manage_users")
    )
    return keyboard


def get_user_confirm_keyboard(user_id: str, role: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения добавления пользователя"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_add_{user_id}_{role}"),
        InlineKeyboardButton("❌ Отмена", callback_data="admin_add_user"),
        InlineKeyboardButton("🔙 Назад", callback_data="admin_manage_users")
    )
    return keyboard


def get_user_action_keyboard(user_id: str) -> InlineKeyboardMarkup:
    """Клавиатура действий с конкретным пользователем"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✏️ Изменить роль", callback_data=f"change_role_{user_id}"),
        InlineKeyboardButton("🚫 Заблокировать", callback_data=f"block_user_{user_id}"),
        InlineKeyboardButton("✅ Разблокировать", callback_data=f"unblock_user_{user_id}"),
        InlineKeyboardButton("📋 История действий", callback_data=f"user_history_{user_id}"),
        InlineKeyboardButton("🔙 Назад", callback_data="admin_manage_users")
    )
    return keyboard


def get_role_change_keyboard(user_id: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора новой роли для пользователя"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("👑 Администратор", callback_data=f"set_role_{user_id}_admin"),
        InlineKeyboardButton("🔧 Координатор", callback_data=f"set_role_{user_id}_coordinator"),
        InlineKeyboardButton("📢 Промо", callback_data=f"set_role_{user_id}_promo"),
        InlineKeyboardButton("👤 Пользователь", callback_data=f"set_role_{user_id}_user"),
        InlineKeyboardButton("🔙 Назад", callback_data=f"user_actions_{user_id}")
    )
    return keyboard


def get_user_list_keyboard(users: List[Dict[str, Any]], page: int = 0, per_page: int = 10) -> InlineKeyboardMarkup:
    """Клавиатура со списком пользователей (с пагинацией)"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_users = users[start_idx:end_idx]
    
    role_symbols = {
        "admin": "👑",
        "coordinator": "🔧", 
        "promo": "📢",
        "user": "👤"
    }
    
    for user in page_users:
        user_id = user["user_id"]
        symbol = role_symbols.get(user["role"], "❓")
        blocked_mark = " 🚫" if user.get("blocked", False) else ""
        name = user.get("first_name", "Unknown")[:20]  # Ограничиваем длину
        
        keyboard.add(InlineKeyboardButton(
            f"{symbol} {name}{blocked_mark}",
            callback_data=f"user_actions_{user_id}"
        ))
    
    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"users_page_{page-1}"))
    if end_idx < len(users):
        nav_buttons.append(InlineKeyboardButton("➡️ Далее", callback_data=f"users_page_{page+1}"))
    
    if nav_buttons:
        keyboard.add(*nav_buttons)
    
    keyboard.add(InlineKeyboardButton("🔙 В меню", callback_data="admin_manage_users"))
    return keyboard


def get_search_results_keyboard(results: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура с результатами поиска пользователей"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    role_symbols = {
        "admin": "👑",
        "coordinator": "🔧", 
        "promo": "📢",
        "user": "👤"
    }
    
    for user in results[:10]:  # Показываем максимум 10 результатов
        user_id = user["user_id"]
        symbol = role_symbols.get(user["role"], "❓")
        blocked_mark = " 🚫" if user.get("blocked", False) else ""
        name = user.get("first_name", "Unknown")[:15]
        username = user.get("username", "")
        username_text = f" (@{username})" if username and username != "unknown" else ""
        
        keyboard.add(InlineKeyboardButton(
            f"{symbol} {name}{username_text}{blocked_mark}",
            callback_data=f"user_actions_{user_id}"
        ))
    
    keyboard.add(
        InlineKeyboardButton("🔍 Новый поиск", callback_data="admin_search_users"),
        InlineKeyboardButton("🔙 Назад", callback_data="admin_manage_users")
    )
    return keyboard


def get_block_confirm_keyboard(user_id: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения блокировки пользователя"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🚫 Заблокировать", callback_data=f"confirm_block_{user_id}"),
        InlineKeyboardButton("❌ Отмена", callback_data=f"user_actions_{user_id}")
    )
    return keyboard


def get_pagination_keyboard(current_page: int, total_pages: int, callback_prefix: str) -> InlineKeyboardMarkup:
    """Универсальная клавиатура пагинации"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    buttons = []
    
    # Кнопка "Назад"
    if current_page > 0:
        buttons.append(InlineKeyboardButton("⬅️", callback_data=f"{callback_prefix}_{current_page-1}"))
    
    # Информация о странице
    buttons.append(InlineKeyboardButton(f"{current_page+1}/{total_pages}", callback_data="noop"))
    
    # Кнопка "Вперед"
    if current_page < total_pages - 1:
        buttons.append(InlineKeyboardButton("➡️", callback_data=f"{callback_prefix}_{current_page+1}"))
    
    if buttons:
        keyboard.add(*buttons)
    
    return keyboard
