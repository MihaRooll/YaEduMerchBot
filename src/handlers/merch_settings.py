import logging
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.handler_backends import State, StatesGroup
from typing import Dict, Any, List
from ..storage import storage
from ..auth import role_manager
from ..keyboards import get_back_keyboard

logger = logging.getLogger(__name__)

# Состояния FSM для настроек мерча
class MerchSettingsStates(StatesGroup):
    waiting_for_product_name = State()
    waiting_for_product_type = State()
    waiting_for_product_color = State()
    waiting_for_product_sizes = State()
    waiting_for_quantity = State()
    waiting_for_size_name = State()

# Временное хранилище для данных настройки
merch_data = {}

def register_merch_settings_handlers(bot, chat_manager):
    """Регистрация хэндлеров для настроек мерча"""
    
    @bot.message_handler(commands=['merch'])
    def handle_merch_command(message: Message):
        """Обработчик команды /merch - быстрый доступ к настройкам мерча"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Проверяем права администратора
        if not role_manager.has_permission(user_id, "admin"):
            bot.reply_to(message, "❌ У вас нет прав для настройки мерча")
            return
        
        # Показываем меню настроек мерча
        _show_merch_settings_menu(bot, chat_id, user_id, chat_manager)
    
    @bot.message_handler(state=MerchSettingsStates.waiting_for_product_name)
    def handle_product_name_input(message: Message):
        """Обработчик ввода названия товара"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        logger.info(f"🎯 FSM обработчик waiting_for_product_name сработал!")
        logger.info(f"🎯 Получено название товара: '{message.text}' от пользователя {user_id}")
        logger.info(f"🎯 Текущее состояние пользователя: {bot.get_state(user_id, chat_id)}")
        logger.info(f"🎯 Ожидаемое состояние: {MerchSettingsStates.waiting_for_product_name}")
        logger.info(f"🎯 Проверяем права пользователя {user_id}")
        logger.info(f"🎯 Сообщение получено в чате {chat_id}")
        
        if not role_manager.has_permission(user_id, "admin"):
            logger.warning(f"Пользователь {user_id} не имеет прав администратора")
            bot.reply_to(message, "❌ У вас нет прав для настройки мерча")
            return
        
        logger.info(f"✅ Права администратора подтверждены для пользователя {user_id}")
        
        product_name = message.text.strip()
        if len(product_name) < 3:
            logger.info(f"Название товара слишком короткое: '{product_name}'")
            bot.reply_to(message, "❌ Название товара должно содержать минимум 3 символа")
            return
        
        logger.info(f"✅ Название товара валидно: '{product_name}'")
        
        # Сохраняем название товара
        if user_id not in merch_data:
            merch_data[user_id] = {}
        merch_data[user_id]['name'] = product_name
        
        logger.info(f"✅ Сохранено название товара: '{product_name}' для пользователя {user_id}")
        logger.info(f"✅ Временные данные: {merch_data[user_id]}")
        
        # Переходим к выбору типа товара
        logger.info(f"🔄 Переходим к состоянию waiting_for_product_type для пользователя {user_id}")
        bot.set_state(user_id, MerchSettingsStates.waiting_for_product_type, chat_id)
        logger.info(f"✅ Новое состояние установлено: {bot.get_state(user_id, chat_id)}")
        
        # Показываем следующий шаг
        logger.info(f"🔄 Показываем выбор типа товара для пользователя {user_id}")
        _show_product_type_selection(bot, chat_id, user_id, chat_manager)
    
    @bot.message_handler(state=MerchSettingsStates.waiting_for_product_type)
    def handle_product_type_input(message: Message):
        """Обработчик ввода типа товара"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if not role_manager.has_permission(user_id, "admin"):
            bot.reply_to(message, "❌ У вас нет прав для настройки мерча")
            return
        
        product_type = message.text.strip().lower()
        valid_types = ['longsleeve', 'tshirt', 'hoodie', 'sweatshirt', 'other']
        
        if product_type not in valid_types:
            bot.reply_to(message, f"❌ Неверный тип товара. Доступные типы: {', '.join(valid_types)}")
            return
        
        # Сохраняем тип товара
        merch_data[user_id]['type'] = product_type
        
        # Переходим к выбору цвета
        bot.set_state(user_id, MerchSettingsStates.waiting_for_product_color, chat_id)
        _show_color_selection(bot, chat_id, user_id, chat_manager)
    
    @bot.message_handler(state=MerchSettingsStates.waiting_for_product_color)
    def handle_product_color_input(message: Message):
        """Обработчик ввода цвета товара"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if not role_manager.has_permission(user_id, "admin"):
            bot.reply_to(message, "❌ У вас нет прав для настройки мерча")
            return
        
        color = message.text.strip().lower()
        valid_colors = ['white', 'black', 'gray', 'blue', 'red', 'green', 'yellow', 'pink', 'purple', 'orange']
        
        if color not in valid_colors:
            bot.reply_to(message, f"❌ Неверный цвет. Доступные цвета: {', '.join(valid_colors)}")
            return
        
        # Сохраняем цвет товара
        merch_data[user_id]['color'] = color
        
        # Переходим к настройке размеров
        bot.set_state(user_id, MerchSettingsStates.waiting_for_quantity, chat_id)
        _show_size_setup(bot, chat_id, user_id, chat_manager)
    
    @bot.message_handler(state=MerchSettingsStates.waiting_for_quantity)
    def handle_quantity_input(message: Message):
        """Обработчик ввода количества товара"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if not role_manager.has_permission(user_id, "admin"):
            bot.reply_to(message, "❌ У вас нет прав для настройки мерча")
            return
        
        try:
            quantity = int(message.text.strip())
            if quantity <= 0:
                bot.reply_to(message, "❌ Количество должно быть больше 0")
                return
        except ValueError:
            bot.reply_to(message, "❌ Введите корректное число")
            return
        
        # Сохраняем количество для текущего размера
        current_size = merch_data[user_id].get('current_size')
        if current_size:
            if 'sizes' not in merch_data[user_id]:
                merch_data[user_id]['sizes'] = {}
            merch_data[user_id]['sizes'][current_size] = quantity
        
        # Показываем следующий размер или завершаем
        _show_next_size_or_finish(bot, chat_id, user_id, chat_manager)
    
    @bot.message_handler(state=MerchSettingsStates.waiting_for_size_name)
    def handle_size_name_input(message: Message):
        """Обработчик ввода названия размера"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        logger.info(f"🎯 FSM обработчик waiting_for_size_name сработал!")
        logger.info(f"🎯 Получено название размера: '{message.text}' от пользователя {user_id}")
        
        if not role_manager.has_permission(user_id, "admin"):
            logger.warning(f"Пользователь {user_id} не имеет прав администратора")
            bot.reply_to(message, "❌ У вас нет прав для настройки мерча")
            return
        
        size_name = message.text.strip().upper()
        if len(size_name) < 1 or len(size_name) > 5:
            bot.reply_to(message, "❌ Название размера должно содержать от 1 до 5 символов")
            return
        
        # Проверяем, не существует ли уже такой размер
        inventory = storage.get_all("inventory.json")
        existing_sizes = inventory.get('sizes', {})
        
        if size_name in existing_sizes:
            bot.reply_to(message, f"❌ Размер {size_name} уже существует")
            return
        
        # Добавляем новый размер в инвентарь
        if 'sizes' not in inventory:
            inventory['sizes'] = {}
        
        inventory['sizes'][size_name] = {
            'qty_total': 0,
            'qty_reserved': 0
        }
        
        # Сохраняем обновленный инвентарь
        success = storage.save_json_atomic("inventory.json", inventory)
        
        if success:
            content = f"✅ Размер <b>{size_name}</b> успешно добавлен!\n\n"
            content += "Теперь вы можете использовать этот размер при создании товаров."
            
            # Сбрасываем состояние
            bot.delete_state(user_id, chat_id)
            
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton("➕ Добавить еще размер", callback_data="merch_add_size"),
                InlineKeyboardButton("📏 Управление размерами", callback_data="merch_manage_sizes"),
                InlineKeyboardButton("🔙 Назад", callback_data="merch_general_settings")
            )
            
            chat_manager.update_chat_message(chat_id, content, keyboard)
        else:
            bot.reply_to(message, "❌ Ошибка при сохранении размера. Попробуйте снова.")
    
    @bot.callback_query_handler(func=lambda call: call.data == "merch_manage_sizes")
    def handle_manage_sizes(call: CallbackQuery):
        """Обработчик управления размерами"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        if not role_manager.has_permission(user_id, "admin"):
            bot.answer_callback_query(call.id, "❌ Нет прав администратора!")
            return
        
        _show_sizes_management(bot, chat_id, user_id, chat_manager)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "merch_manage_colors")
    def handle_manage_colors(call: CallbackQuery):
        """Обработчик управления цветами"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        if not role_manager.has_permission(user_id, "admin"):
            bot.answer_callback_query(call.id, "❌ Нет прав администратора!")
            return
        
        _show_colors_management(bot, chat_id, user_id, chat_manager)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "merch_order_stats")
    def handle_order_stats(call: CallbackQuery):
        """Обработчик статистики заказов"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        if not role_manager.has_permission(user_id, "admin"):
            bot.answer_callback_query(call.id, "❌ Нет прав администратора!")
            return
        
        _show_order_statistics(bot, chat_id, user_id, chat_manager)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "merch_general_settings")
    def handle_general_settings(call: CallbackQuery):
        """Обработчик общих настроек мерча"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        if not role_manager.has_permission(user_id, "admin"):
            bot.answer_callback_query(call.id, "❌ Нет прав администратора!")
            return
        
        _show_general_merch_settings(bot, chat_id, user_id, chat_manager)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "merch_add_product")
    def handle_add_product(call: CallbackQuery):
        """Обработчик добавления товара"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        logger.info(f"🎯 Пользователь {user_id} нажал кнопку добавления товара")
        logger.info(f"🎯 Chat ID: {chat_id}")
        
        if not role_manager.has_permission(user_id, "admin"):
            logger.warning(f"❌ Пользователь {user_id} не имеет прав администратора")
            bot.answer_callback_query(call.id, "❌ Нет прав администратора!")
            return
        
        logger.info(f"✅ Права администратора подтверждены для пользователя {user_id}")
        
        # Очищаем временные данные
        if user_id in merch_data:
            logger.info(f"🗑️ Очищаем старые временные данные для пользователя {user_id}")
            del merch_data[user_id]
        
        # Устанавливаем состояние и показываем форму
        logger.info(f"🔄 Устанавливаем состояние waiting_for_product_name для пользователя {user_id}")
        bot.set_state(user_id, MerchSettingsStates.waiting_for_product_name, chat_id)
        
        # Проверяем, что состояние установилось
        current_state = bot.get_state(user_id, chat_id)
        logger.info(f"✅ Состояние установлено: {current_state}")
        logger.info(f"✅ Ожидаемое состояние: {MerchSettingsStates.waiting_for_product_name}")
        logger.info(f"✅ Chat ID для состояния: {chat_id}")
        
        if current_state == MerchSettingsStates.waiting_for_product_name:
            logger.info(f"✅ Состояние успешно установлено!")
            _show_add_product_form(bot, chat_id, user_id, chat_manager)
        else:
            logger.info(f"ℹ️ Состояние установлено, но не совпадает с ожидаемым. Текущее: {current_state}")
            # Все равно показываем форму, так как состояние установлено
            _show_add_product_form(bot, chat_id, user_id, chat_manager)
        
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "merch_view_products")
    def handle_view_products(call: CallbackQuery):
        """Обработчик просмотра товаров"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        if not role_manager.has_permission(user_id, "admin"):
            bot.answer_callback_query(call.id, "❌ Нет прав администратора!")
            return
        
        _show_products_list(bot, chat_id, user_id, chat_manager)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("merch_product_"))
    def handle_product_actions(call: CallbackQuery):
        """Обработчик действий с товарами"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        if not role_manager.has_permission(user_id, "admin"):
            bot.answer_callback_query(call.id, "❌ Нет прав администратора!")
            return
        
        action = call.data.replace("merch_product_", "")
        
        if action.startswith("toggle_"):
            product_id = action.replace("toggle_", "")
            _toggle_product_status(bot, chat_id, user_id, product_id, chat_manager)
        elif action.startswith("edit_"):
            product_id = action.replace("edit_", "")
            _show_edit_product_form(bot, chat_id, user_id, product_id, chat_manager)
        elif action.startswith("delete_"):
            product_id = action.replace("delete_", "")
            _show_delete_product_confirm(bot, chat_id, user_id, product_id, chat_manager)
        
        bot.answer_callback_query(call.id)
    
    # Обработчики управления размерами
    @bot.callback_query_handler(func=lambda call: call.data == "merch_add_size")
    def handle_add_size(call: CallbackQuery):
        """Обработчик добавления размера"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        if not role_manager.has_permission(user_id, "admin"):
            bot.answer_callback_query(call.id, "❌ Нет прав администратора!")
            return
        
        # Устанавливаем состояние для добавления размера
        bot.set_state(user_id, MerchSettingsStates.waiting_for_size_name, chat_id)
        _show_add_size_form(bot, chat_id, user_id, chat_manager)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "merch_remove_size")
    def handle_remove_size(call: CallbackQuery):
        """Обработчик удаления размера"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        if not role_manager.has_permission(user_id, "admin"):
            bot.answer_callback_query(call.id, "❌ Нет прав администратора!")
            return
        
        _show_remove_size_selection(bot, chat_id, user_id, chat_manager)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "merch_edit_sizes")
    def handle_edit_sizes(call: CallbackQuery):
        """Обработчик редактирования размеров"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        if not role_manager.has_permission(user_id, "admin"):
            bot.answer_callback_query(call.id, "❌ Нет прав администратора!")
            return
        
        _show_edit_sizes_form(bot, chat_id, user_id, chat_manager)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("merch_delete_size_"))
    def handle_delete_size_confirm(call: CallbackQuery):
        """Обработчик подтверждения удаления размера"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        if not role_manager.has_permission(user_id, "admin"):
            bot.answer_callback_query(call.id, "❌ Нет прав администратора!")
            return
        
        size_to_delete = call.data.replace("merch_delete_size_", "")
        _show_delete_size_confirm(bot, chat_id, user_id, size_to_delete, chat_manager)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("merch_confirm_delete_size_"))
    def handle_confirm_delete_size(call: CallbackQuery):
        """Обработчик подтверждения удаления размера"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        if not role_manager.has_permission(user_id, "admin"):
            bot.answer_callback_query(call.id, "❌ Нет прав администратора!")
            return
        
        size_to_delete = call.data.replace("merch_confirm_delete_size_", "")
        _delete_size(bot, chat_id, user_id, size_to_delete, chat_manager)
        bot.answer_callback_query(call.id)
    


# Вспомогательные функции
def _show_merch_settings_menu(bot, chat_id: int, user_id: int, chat_manager):
    """Показывает главное меню настроек мерча"""
    content = "🛍 <b>Настройки мерча</b>\n\n"
    content += "Управление товарами и настройками:\n\n"
    content += "📦 <b>Товары:</b> Добавление, редактирование, удаление\n"
    content += "📏 <b>Размеры:</b> Управление доступными размерами\n"
    content += "🎨 <b>Цвета:</b> Управление цветовой палитрой\n"
    content += "📊 <b>Статистика:</b> Анализ заказов и остатков\n"
    content += "⚙️ <b>Общие:</b> Основные параметры системы"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Добавить товар", callback_data="merch_add_product"),
        InlineKeyboardButton("📋 Список товаров", callback_data="merch_view_products"),
        InlineKeyboardButton("📏 Управление размерами", callback_data="merch_manage_sizes"),
        InlineKeyboardButton("🎨 Управление цветами", callback_data="merch_manage_colors"),
        InlineKeyboardButton("📊 Статистика заказов", callback_data="merch_order_stats"),
        InlineKeyboardButton("⚙️ Общие настройки", callback_data="merch_general_settings"),
        InlineKeyboardButton("🔙 Назад", callback_data="admin_merch_settings")
    )
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_add_product_form(bot, chat_id: int, user_id: int, chat_manager):
    """Показывает форму добавления товара"""
    content = "➕ <b>Добавление нового товара</b>\n\n"
    content += "Введите название товара (например: Лонгслив белый):"
    
    keyboard = get_back_keyboard("merch_general_settings")
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_product_type_selection(bot, chat_id: int, user_id: int, chat_manager):
    """Показывает выбор типа товара"""
    content = "📋 <b>Выберите тип товара:</b>\n\n"
    content += "Доступные типы:\n"
    content += "• longsleeve - Лонгслив\n"
    content += "• tshirt - Футболка\n"
    content += "• hoodie - Худи\n"
    content += "• sweatshirt - Свитшот\n"
    content += "• other - Другое\n\n"
    content += "Введите тип товара:"
    
    keyboard = get_back_keyboard("merch_general_settings")
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_color_selection(bot, chat_id: int, user_id: int, chat_manager):
    """Показывает выбор цвета товара"""
    content = "🎨 <b>Выберите цвет товара:</b>\n\n"
    content += "Доступные цвета:\n"
    content += "• white - Белый\n"
    content += "• black - Черный\n"
    content += "• gray - Серый\n"
    content += "• blue - Синий\n"
    content += "• red - Красный\n"
    content += "• green - Зеленый\n"
    content += "• yellow - Желтый\n"
    content += "• pink - Розовый\n"
    content += "• purple - Фиолетовый\n"
    content += "• orange - Оранжевый\n\n"
    content += "Введите цвет товара:"
    
    keyboard = get_back_keyboard("merch_general_settings")
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_size_setup(bot, chat_id: int, user_id: int, chat_manager):
    """Показывает настройку размеров"""
    # Получаем доступные размеры из инвентаря
    inventory = storage.get_all("inventory.json")
    available_sizes = list(inventory.get('sizes', {}).keys())
    
    if not available_sizes:
        content = "❌ <b>Ошибка настройки размеров</b>\n\n"
        content += "В системе не настроено ни одного размера.\n\n"
        content += "Сначала настройте размеры в разделе «Управление размерами»."
        
        keyboard = get_back_keyboard("merch_general_settings")
        chat_manager.update_chat_message(chat_id, content, keyboard)
        return
    
    content = "📏 <b>Настройка размеров товара</b>\n\n"
    content += "Теперь нужно настроить размеры и количество для каждого размера.\n\n"
    content += f"Доступные размеры: {', '.join(sorted(available_sizes))}\n\n"
    content += f"Начнем с размера {available_sizes[0]}. Введите количество товара для размера {available_sizes[0]}:"
    
    # Сохраняем текущий размер
    if user_id not in merch_data:
        merch_data[user_id] = {}
    merch_data[user_id]['current_size'] = available_sizes[0]
    merch_data[user_id]['sizes_to_setup'] = available_sizes.copy()
    
    keyboard = get_back_keyboard("merch_general_settings")
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_next_size_or_finish(bot, chat_id: int, user_id: int, chat_manager):
    """Показывает следующий размер или завершает создание"""
    user_data = merch_data.get(user_id, {})
    sizes_to_setup = user_data.get('sizes_to_setup', [])
    current_size = user_data.get('current_size')
    
    # Убираем текущий размер из списка
    if current_size in sizes_to_setup:
        sizes_to_setup.remove(current_size)
    
    if sizes_to_setup:
        # Показываем следующий размер
        next_size = sizes_to_setup[0]
        user_data['current_size'] = next_size
        merch_data[user_id] = user_data
        
        content = f"📏 <b>Размер {next_size}</b>\n\n"
        content += f"Введите количество товара для размера {next_size}:"
        
        keyboard = get_back_keyboard("merch_general_settings")
        chat_manager.update_chat_message(chat_id, content, keyboard)
    else:
        # Завершаем создание товара
        _finish_product_creation(bot, chat_id, user_id, chat_manager)

def _finish_product_creation(bot, chat_id: int, user_id: int, chat_manager):
    """Завершает создание товара"""
    user_data = merch_data.get(user_id, {})
    
    if not all(key in user_data for key in ['name', 'type', 'color', 'sizes']):
        content = "❌ <b>Ошибка создания товара</b>\n\n"
        content += "Не все данные были заполнены. Попробуйте снова."
        keyboard = get_back_keyboard("merch_add_product")
        chat_manager.update_chat_message(chat_id, content, keyboard)
        return
    
    # Создаем товар в базе данных
    product_id = f"{user_data['type']}_{user_data['color']}"
    success = storage.add_product(
        product_id=product_id,
        name=user_data['name'],
        product_type=user_data['type'],
        base_color=user_data['color'],
        sizes=user_data['sizes']
    )
    
    if success:
        content = "✅ <b>Товар успешно создан!</b>\n\n"
        content += f"📦 <b>Название:</b> {user_data['name']}\n"
        content += f"🔧 <b>Тип:</b> {user_data['type']}\n"
        content += f"🎨 <b>Цвет:</b> {user_data['color']}\n"
        content += f"📏 <b>Размеры:</b> {', '.join(user_data['sizes'].keys())}\n"
        content += f"📊 <b>Общее количество:</b> {sum(user_data['sizes'].values())} шт.\n\n"
        content += "Товар добавлен в инвентарь и готов к использованию!"
        
        # Очищаем временные данные
        del merch_data[user_id]
        
        # Сбрасываем состояние
        bot.delete_state(user_id, chat_id)
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("➕ Добавить еще товар", callback_data="merch_add_product"),
            InlineKeyboardButton("📋 Список товаров", callback_data="merch_view_products"),
            InlineKeyboardButton("🔙 Назад", callback_data="merch_general_settings")
        )
        
        chat_manager.update_chat_message(chat_id, content, keyboard)
    else:
        content = "❌ <b>Ошибка создания товара</b>\n\n"
        content += "Не удалось сохранить товар в базе данных. Попробуйте снова."
        keyboard = get_back_keyboard("merch_add_product")
        chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_products_list(bot, chat_id: int, user_id: int, chat_manager):
    """Показывает список товаров"""
    products = storage.list_products()
    
    if not products:
        content = "📋 <b>Список товаров</b>\n\n"
        content += "❌ Товары не найдены\n\n"
        content += "Добавьте первый товар, чтобы начать работу."
        
        keyboard = get_back_keyboard("merch_general_settings")
        chat_manager.update_chat_message(chat_id, content, keyboard)
        return
    
    content = "📋 <b>Список товаров</b>\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for product_id, product in products.items():
        status = "✅" if product.get("active", True) else "❌"
        name = product.get("name", "Без названия")
        product_type = product.get("type", "Неизвестно")
        color = product.get("base_color", "Неизвестно")
        
        # Подсчитываем общее количество
        total_qty = sum(size_data["qty_total"] for size_data in product.get("sizes", {}).values())
        
        content += f"{status} <b>{name}</b>\n"
        content += f"   Тип: {product_type}\n"
        content += f"   Цвет: {color}\n"
        content += f"   Всего: {total_qty} шт.\n\n"
        
        # Кнопки действий для каждого товара
        keyboard.add(
            InlineKeyboardButton(
                f"🔄 {name}",
                callback_data=f"merch_product_toggle_{product_id}"
            ),
            InlineKeyboardButton(
                f"✏️ Редактировать {name}",
                callback_data=f"merch_product_edit_{product_id}"
            ),
            InlineKeyboardButton(
                f"🗑️ Удалить {name}",
                callback_data=f"merch_product_delete_{product_id}"
            )
        )
    
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="merch_general_settings"))
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_sizes_management(bot, chat_id: int, user_id: int, chat_manager):
    """Показывает управление размерами"""
    # Получаем текущие размеры из инвентаря
    inventory = storage.get_all("inventory.json")
    current_sizes = list(inventory.get('sizes', {}).keys())
    
    content = "📏 <b>Управление размерами</b>\n\n"
    content += "Текущие размеры в системе:\n"
    
    if current_sizes:
        for size in sorted(current_sizes):
            content += f"• {size}\n"
    else:
        content += "❌ Размеры не настроены\n"
    
    content += "\nВыберите действие:"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Добавить размер", callback_data="merch_add_size"),
        InlineKeyboardButton("🗑️ Удалить размер", callback_data="merch_remove_size"),
        InlineKeyboardButton("📝 Редактировать размеры", callback_data="merch_edit_sizes"),
        InlineKeyboardButton("🔙 Назад", callback_data="merch_general_settings")
    )
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_colors_management(bot, chat_id: int, user_id: int, chat_manager):
    """Показывает управление цветами"""
    content = "🎨 <b>Управление цветами</b>\n\n"
    content += "Функция управления цветами будет реализована в следующих версиях.\n\n"
    content += "Пока что используйте базовые цвета: white, black, gray, blue, red, green, yellow, pink, purple, orange"
    
    keyboard = get_back_keyboard("merch_general_settings")
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_order_statistics(bot, chat_id: int, user_id: int, chat_manager):
    """Показывает статистику заказов"""
    summary = storage.get_inventory_summary()
    
    content = "📊 <b>Статистика мерча</b>\n\n"
    content += f"📦 <b>Всего товаров:</b> {summary.get('total_products', 0)}\n"
    content += f"✅ <b>Активных товаров:</b> {summary.get('active_products', 0)}\n"
    content += f"📋 <b>Всего единиц:</b> {summary.get('total_items', 0)}\n"
    content += f"🔒 <b>Зарезервировано:</b> {summary.get('reserved_items', 0)}\n"
    content += f"📤 <b>Доступно:</b> {summary.get('total_items', 0) - summary.get('reserved_items', 0)}\n\n"
    
    if summary.get('products'):
        content += "<b>Детали по товарам:</b>\n"
        for product in summary['products'][:5]:  # Показываем первые 5
            status = "✅" if product.get('active') else "❌"
            content += f"{status} {product['name']} ({product['color']})\n"
            for size, size_data in product['sizes'].items():
                content += f"   {size}: {size_data['available']}/{size_data['total']}\n"
            content += "\n"
    
    keyboard = get_back_keyboard("merch_general_settings")
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_general_merch_settings(bot, chat_id: int, user_id: int, chat_manager):
    """Показывает общие настройки мерча"""
    content = "⚙️ <b>Общие настройки мерча</b>\n\n"
    content += "Основные параметры системы мерча:\n\n"
    content += "📦 <b>Товары:</b> Управление ассортиментом\n"
    content += "📏 <b>Размеры:</b> Настройка размерной сетки\n"
    content += "🎨 <b>Цвета:</b> Управление цветовой палитрой\n"
    content += "📊 <b>Остатки:</b> Контроль количества\n\n"
    content += "Выберите раздел для настройки:"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Добавить товар", callback_data="merch_add_product"),
        InlineKeyboardButton("📋 Список товаров", callback_data="merch_view_products"),
        InlineKeyboardButton("📏 Размеры", callback_data="merch_manage_sizes"),
        InlineKeyboardButton("🎨 Цвета", callback_data="merch_manage_colors"),
        InlineKeyboardButton("🔙 Назад", callback_data="merch_general_settings")
    )
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _toggle_product_status(bot, chat_id: int, user_id: int, product_id: str, chat_manager):
    """Переключает статус товара"""
    success = storage.toggle_product_status(product_id)
    
    if success:
        product = storage.get_product(product_id)
        status = "активирован" if product.get("active", True) else "деактивирован"
        content = f"✅ Товар <b>{product.get('name', product_id)}</b> {status}"
    else:
        content = "❌ Не удалось изменить статус товара"
    
    keyboard = get_back_keyboard("merch_view_products")
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_edit_product_form(bot, chat_id: int, user_id: int, product_id: str, chat_manager):
    """Показывает форму редактирования товара"""
    content = "✏️ <b>Редактирование товара</b>\n\n"
    content += "Функция редактирования товаров будет реализована в следующих версиях."
    
    keyboard = get_back_keyboard("merch_view_products")
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_delete_product_confirm(bot, chat_id: int, user_id: int, product_id: str, chat_manager):
    """Показывает подтверждение удаления товара"""
    product = storage.get_product(product_id)
    name = product.get("name", product_id) if product else product_id
    
    content = f"🗑️ <b>Удаление товара</b>\n\n"
    content += f"Вы действительно хотите удалить товар <b>{name}</b>?\n\n"
    content += "⚠️ <b>Внимание:</b> Это действие нельзя отменить!"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Да, удалить", callback_data=f"merch_confirm_delete_{product_id}"),
        InlineKeyboardButton("❌ Отмена", callback_data="merch_view_products")
    )
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

# Функции управления размерами
def _show_add_size_form(bot, chat_id: int, user_id: int, chat_manager):
    """Показывает форму добавления размера"""
    content = "➕ <b>Добавление нового размера</b>\n\n"
    content += "Введите название размера (например: M, L, XL, 2XL):\n\n"
    content += "💡 <b>Совет:</b> Используйте короткие названия размеров"
    
    keyboard = get_back_keyboard("merch_manage_sizes")
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_remove_size_selection(bot, chat_id: int, user_id: int, chat_manager):
    """Показывает выбор размера для удаления"""
    inventory = storage.get_all("inventory.json")
    current_sizes = list(inventory.get('sizes', {}).keys())
    
    if not current_sizes:
        content = "❌ <b>Нет размеров для удаления</b>\n\n"
        content += "В системе не настроено ни одного размера."
        
        keyboard = get_back_keyboard("merch_manage_sizes")
        chat_manager.update_chat_message(chat_id, content, keyboard)
        return
    
    content = "🗑️ <b>Удаление размера</b>\n\n"
    content += "Выберите размер для удаления:\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    for size in sorted(current_sizes):
        keyboard.add(
            InlineKeyboardButton(f"❌ {size}", callback_data=f"merch_delete_size_{size}")
        )
    
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="merch_manage_sizes"))
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_delete_size_confirm(bot, chat_id: int, user_id: int, size_name: str, chat_manager):
    """Показывает подтверждение удаления размера"""
    content = f"🗑️ <b>Удаление размера</b>\n\n"
    content += f"Вы действительно хотите удалить размер <b>{size_name}</b>?\n\n"
    content += "⚠️ <b>Внимание:</b> Это действие нельзя отменить!\n"
    content += "Все товары с этим размером также будут удалены!"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Да, удалить", callback_data=f"merch_confirm_delete_size_{size_name}"),
        InlineKeyboardButton("❌ Отмена", callback_data="merch_manage_sizes")
    )
    
    chat_manager.update_chat_message(chat_id, content, keyboard)

def _delete_size(bot, chat_id: int, user_id: int, size_name: str, chat_manager):
    """Удаляет размер из системы"""
    try:
        # Получаем текущий инвентарь
        inventory = storage.get_all("inventory.json")
        current_sizes = inventory.get('sizes', {})
        
        if size_name not in current_sizes:
            content = f"❌ Размер <b>{size_name}</b> не найден"
            keyboard = get_back_keyboard("merch_manage_sizes")
            chat_manager.update_chat_message(chat_id, content, keyboard)
            return
        
        # Удаляем размер из инвентаря
        del current_sizes[size_name]
        inventory['sizes'] = current_sizes
        
        # Удаляем размер из всех товаров
        products = inventory.get('products', {})
        for product_id, product in products.items():
            if 'sizes' in product and size_name in product['sizes']:
                del product['sizes'][size_name]
        
        # Сохраняем обновленный инвентарь
        success = storage.save_json_atomic("inventory.json", inventory)
        
        if success:
            content = f"✅ Размер <b>{size_name}</b> успешно удален!\n\n"
            content += "Размер удален из всех товаров и инвентаря."
            
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton("🗑️ Удалить еще размер", callback_data="merch_remove_size"),
                InlineKeyboardButton("📏 Управление размерами", callback_data="merch_manage_sizes"),
                InlineKeyboardButton("🔙 Назад", callback_data="merch_general_settings")
            )
            
            chat_manager.update_chat_message(chat_id, content, keyboard)
        else:
            content = "❌ Ошибка при удалении размера. Попробуйте снова."
            keyboard = get_back_keyboard("merch_manage_sizes")
            chat_manager.update_chat_message(chat_id, content, keyboard)
            
    except Exception as e:
        logger.error(f"Ошибка при удалении размера {size_name}: {e}")
        content = "❌ Произошла ошибка при удалении размера"
        keyboard = get_back_keyboard("merch_manage_sizes")
        chat_manager.update_chat_message(chat_id, content, keyboard)

def _show_edit_sizes_form(bot, chat_id: int, user_id: int, chat_manager):
    """Показывает форму редактирования размеров"""
    inventory = storage.get_all("inventory.json")
    current_sizes = list(inventory.get('sizes', {}).keys())
    
    if not current_sizes:
        content = "❌ <b>Нет размеров для редактирования</b>\n\n"
        content += "В системе не настроено ни одного размера."
        
        keyboard = get_back_keyboard("merch_manage_sizes")
        chat_manager.update_chat_message(chat_id, content, keyboard)
        return
    
    content = "📝 <b>Редактирование размеров</b>\n\n"
    content += "Текущие размеры в системе:\n"
    
    for size in sorted(current_sizes):
        content += f"• {size}\n"
    
    content += "\n💡 <b>Примечание:</b> Для изменения названия размера удалите старый и создайте новый."
    
    keyboard = get_back_keyboard("merch_manage_sizes")
    
    chat_manager.update_chat_message(chat_id, content, keyboard)
