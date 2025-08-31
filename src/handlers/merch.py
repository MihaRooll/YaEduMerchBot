import logging
from telebot.types import Message, CallbackQuery
from telebot.handler_backends import State, StatesGroup
from typing import Dict, Any, List
from ..storage import storage
from ..auth import role_manager
from ..keyboards import get_back_keyboard
from datetime import datetime

logger = logging.getLogger(__name__)

# Определяем состояния FSM
class OrderStates(StatesGroup):
    start = State()
    pick_size = State()
    pick_color = State()
    await_image = State()
    review = State()
    pick_chats = State()
    confirm = State()

# Временное хранилище для данных заказов (в реальном проекте лучше использовать Redis)
order_data = {}

def register_merch_handlers(bot, chat_manager):
    """Регистрация хэндлеров для мерча"""
    
    @bot.message_handler(commands=['order'])
    def handle_order_command(message: Message):
        """Обработчик команды /order - начало создания заказа"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Проверяем права пользователя
        if not _can_create_order(user_id):
            bot.reply_to(message, "❌ У вас нет прав для создания заказа")
            return
        
        # Начинаем FSM
        bot.set_state(user_id, OrderStates.start, chat_id)
        _show_order_start(bot, chat_id, user_id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "user_create_order")
    def handle_create_order_callback(call: CallbackQuery):
        """Обработчик кнопки 'Создать заказ'"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        # Проверяем права пользователя
        if not _can_create_order(user_id):
            bot.answer_callback_query(call.id, "❌ У вас нет прав для создания заказа")
            return
        
        # Начинаем FSM
        bot.set_state(user_id, OrderStates.start, chat_id)
        _show_order_start(bot, chat_id, user_id)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "order_start")
    def handle_order_start_callback(call: CallbackQuery):
        """Обработчик кнопки 'Сделать заказ'"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        # Переходим к выбору размера
        bot.set_state(user_id, OrderStates.pick_size, chat_id)
        _show_size_selection(bot, chat_id, user_id)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("size_"))
    def handle_size_selection(call: CallbackQuery):
        """Обработчик выбора размера"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        size = call.data.replace("size_", "")
        
        # Сохраняем выбранный размер
        if user_id not in order_data:
            order_data[user_id] = {}
        order_data[user_id]['size'] = size
        
        # Проверяем, есть ли цвета для этого размера
        colors = storage.list_colors(size)
        if colors and len(colors) > 1 and colors[0] != "_":
            # Переходим к выбору цвета
            bot.set_state(user_id, OrderStates.pick_color, chat_id)
            _show_color_selection(bot, chat_id, user_id, size, colors)
        else:
            # Пропускаем выбор цвета, переходим к загрузке фото
            bot.set_state(user_id, OrderStates.await_image, chat_id)
            _show_image_upload(bot, chat_id, user_id)
        
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("color_"))
    def handle_color_selection(call: CallbackQuery):
        """Обработчик выбора цвета"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        # Парсим callback_data: color_<color>_<size>
        parts = call.data.split("_")
        if len(parts) >= 3:
            color = parts[1]
            size = parts[2]
            
            # Сохраняем выбранный цвет
            if user_id not in order_data:
                order_data[user_id] = {}
            order_data[user_id]['color'] = color
            order_data[user_id]['size'] = size
            
            # Переходим к загрузке фото
            bot.set_state(user_id, OrderStates.await_image, chat_id)
            _show_image_upload(bot, chat_id, user_id)
        
        bot.answer_callback_query(call.id)
    
    @bot.message_handler(content_types=['photo'], state=OrderStates.await_image)
    def handle_photo_upload(message: Message):
        """Обработчик загрузки фото"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Получаем file_id последнего (самого большого) фото
        photo = message.photo[-1]
        file_id = photo.file_id
        
        # Сохраняем file_id
        if user_id not in order_data:
            order_data[user_id] = {}
        order_data[user_id]['photo_file_id'] = file_id
        
        # Переходим к предпросмотру
        bot.set_state(user_id, OrderStates.review, chat_id)
        _show_order_review(bot, chat_id, user_id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "order_change_size", state=OrderStates.review)
    def handle_change_size(call: CallbackQuery):
        """Обработчик изменения размера"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        # Возвращаемся к выбору размера
        bot.set_state(user_id, OrderStates.pick_size, chat_id)
        _show_size_selection(bot, chat_id, user_id)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "order_change_photo", state=OrderStates.review)
    def handle_change_photo(call: CallbackQuery):
        """Обработчик изменения фото"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        # Возвращаемся к загрузке фото
        bot.set_state(user_id, OrderStates.await_image, chat_id)
        _show_image_upload(bot, chat_id, user_id)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "order_change_color", state=OrderStates.review)
    def handle_change_color(call: CallbackQuery):
        """Обработчик изменения цвета"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        # Возвращаемся к выбору цвета
        if user_id in order_data and 'size' in order_data[user_id]:
            size = order_data[user_id]['size']
            colors = storage.list_colors(size)
            if colors and len(colors) > 1 and colors[0] != "_":
                bot.set_state(user_id, OrderStates.pick_color, chat_id)
                _show_color_selection(bot, chat_id, user_id, size, colors)
            else:
                # Если цветов нет, возвращаемся к размеру
                bot.set_state(user_id, OrderStates.pick_size, chat_id)
                _show_size_selection(bot, chat_id, user_id)
        else:
            # Если нет данных о размере, возвращаемся к размеру
            bot.set_state(user_id, OrderStates.pick_size, chat_id)
            _show_size_selection(bot, chat_id, user_id)
        
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "order_select_chats", state=OrderStates.review)
    def handle_select_chats(call: CallbackQuery):
        """Обработчик выбора чатов"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        # Переходим к выбору чатов
        bot.set_state(user_id, OrderStates.pick_chats, chat_id)
        _show_chat_selection(bot, chat_id, user_id)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("chat_toggle_"), state=OrderStates.pick_chats)
    def handle_chat_toggle(call: CallbackQuery):
        """Обработчик переключения чата"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        target_chat_id = call.data.replace("chat_toggle_", "")
        
        # Инициализируем список выбранных чатов
        if user_id not in order_data:
            order_data[user_id] = {}
        if 'selected_chats' not in order_data[user_id]:
            order_data[user_id]['selected_chats'] = []
        
        # Переключаем чат
        if target_chat_id in order_data[user_id]['selected_chats']:
            order_data[user_id]['selected_chats'].remove(target_chat_id)
        else:
            order_data[user_id]['selected_chats'].append(target_chat_id)
        
        # Обновляем отображение
        _show_chat_selection(bot, chat_id, user_id)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "chats_selected", state=OrderStates.pick_chats)
    def handle_chats_selected(call: CallbackQuery):
        """Обработчик завершения выбора чатов"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        # Проверяем, что выбран хотя бы один чат
        if user_id not in order_data or 'selected_chats' not in order_data[user_id] or not order_data[user_id]['selected_chats']:
            bot.answer_callback_query(call.id, "❌ Выберите хотя бы один чат!")
            return
        
        # Переходим к подтверждению
        bot.set_state(user_id, OrderStates.confirm, chat_id)
        _show_order_confirmation(bot, chat_id, user_id)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "order_final_confirm", state=OrderStates.confirm)
    def handle_order_confirmation(call: CallbackQuery):
        """Обработчик финального подтверждения заказа"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        # Создаем заказ
        success = _create_order(user_id)
        if success:
            # Получаем ID заказа для квитанции
            order_id = storage.next_order_id() - 1  # Текущий ID будет следующим
            
            # Сохраняем данные для квитанции
            order_info = order_data.get(user_id, {})
            
            # Очищаем состояние
            bot.delete_state(user_id, chat_id)
            if user_id in order_data:
                del order_data[user_id]
            
            # Показываем квитанцию
            receipt_text = f"✅ <b>Заказ #{order_id} подготовлен к отправке!</b>\n\n"
            receipt_text += f"📏 Размер: {order_info.get('size', 'Неизвестно')}\n"
            if order_info.get('color') and order_info.get('color') != '_':
                receipt_text += f"🎨 Цвет: {order_info.get('color')}\n"
            receipt_text += f"📷 Фото: Загружено\n"
            receipt_text += f"👤 Автор: {role_manager.get_user_data(user_id)['first_name']}\n\n"
            receipt_text += "📤 Заказ будет отправлен в выбранные чаты в ближайшее время."
            
            bot.send_message(chat_id, receipt_text, parse_mode='HTML')
        else:
            # Показываем ошибку с предложением сменить размер/цвет
            error_text = "❌ <b>Не удалось создать заказ</b>\n\n"
            error_text += "Возможные причины:\n"
            error_text += "• Недостаточно товара в наличии\n"
            error_text += "• Ошибка резервирования\n\n"
            error_text += "Попробуйте:\n"
            error_text += "• Сменить размер\n"
            error_text += "• Сменить цвет\n"
            error_text += "• Обратиться к администратору"
            
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton("🔁 Сменить размер", callback_data="order_change_size"),
                InlineKeyboardButton("🎨 Сменить цвет", callback_data="order_change_color"),
                InlineKeyboardButton("🔙 Назад", callback_data="order_back_to_start")
            )
            
            bot.send_message(chat_id, error_text, reply_markup=keyboard, parse_mode='HTML')
    
    @bot.callback_query_handler(func=lambda call: call.data == "order_back_to_start", state="*")
    def handle_back_to_start(call: CallbackQuery):
        """Обработчик возврата к началу"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        # Очищаем состояние и данные
        bot.delete_state(user_id, chat_id)
        if user_id in order_data:
            del order_data[user_id]
        
        # Показываем главное меню
        chat_manager.show_main_menu(chat_id, user_id, role_manager.get_user_role(user_id))
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "order_change_color", state="*")
    def handle_change_color_anywhere(call: CallbackQuery):
        """Обработчик изменения цвета из любого состояния"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        # Возвращаемся к выбору цвета
        if user_id in order_data and 'size' in order_data[user_id]:
            size = order_data[user_id]['size']
            colors = storage.list_colors(size)
            if colors and len(colors) > 1 and colors[0] != "_":
                bot.set_state(user_id, OrderStates.pick_color, chat_id)
                _show_color_selection(bot, chat_id, user_id, size, colors)
            else:
                # Если цветов нет, возвращаемся к размеру
                bot.set_state(user_id, OrderStates.pick_size, chat_id)
                _show_size_selection(bot, chat_id, user_id)
        else:
            # Если нет данных о размере, возвращаемся к размеру
            bot.set_state(user_id, OrderStates.pick_size, chat_id)
            _show_size_selection(bot, chat_id, user_id)
        
        bot.answer_callback_query(call.id)

# Вспомогательные функции
def _can_create_order(user_id: int) -> bool:
    """Проверяет, может ли пользователь создать заказ"""
    user_data = role_manager.get_user_data(user_id)
    if not user_data:
        return False
    
    # Проверяем роль
    role = user_data.get('role', 'user')
    if role in ['admin', 'coordinator', 'promo']:
        return True
    
    # Для обычных пользователей проверяем лимит заказов
    if role == 'user':
        total_orders = user_data.get('total_orders', 0)
        return total_orders < 1
    
    return False

def _show_order_start(bot, chat_id: int, user_id: int):
    """Показывает стартовый экран заказа"""
    text = "🛍 <b>Создание заказа</b>\n\n"
    text += "Добро пожаловать в мастер создания заказов!\n\n"
    text += "Мы поможем вам оформить заказ на мерч Я.Образования.\n"
    text += "Просто следуйте инструкциям и выберите нужные параметры."
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🚀 Сделать заказ", callback_data="order_start"),
        InlineKeyboardButton("🔙 Назад", callback_data="order_back_to_start")
    )
    
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='HTML')

def _show_size_selection(bot, chat_id: int, user_id: int):
    """Показывает выбор размера"""
    sizes = storage.list_sizes()
    
    text = "📏 <b>Выберите размер</b>\n\n"
    text += "Доступные размеры:\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    for size in sizes:
        # Получаем количество доступных товаров
        colors = storage.list_colors(size)
        total_available = 0
        for color in colors:
            if color == "_":
                qty = storage._read_file("inventory.json")['sizes'][size]['colors']['_']
                total_available += qty['qty_total'] - qty['qty_reserved']
            else:
                qty = storage._read_file("inventory.json")['sizes'][size]['colors'][color]
                total_available += qty['qty_total'] - qty['qty_reserved']
        
        text += f"• {size} (осталось {total_available})\n"
        keyboard.add(InlineKeyboardButton(f"{size} ({total_available})", callback_data=f"size_{size}"))
    
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="order_back_to_start"))
    
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='HTML')

def _show_color_selection(bot, chat_id: int, user_id: int, size: str, colors: List[str]):
    """Показывает выбор цвета"""
    text = f"🎨 <b>Выберите цвет для размера {size}</b>\n\n"
    text += "Доступные цвета:\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    for color in colors:
        if color != "_":
            qty = storage._read_file("inventory.json")['sizes'][size]['colors'][color]
            available = qty['qty_total'] - qty['qty_reserved']
            text += f"• {color} (осталось {available})\n"
            keyboard.add(InlineKeyboardButton(f"{color} ({available})", callback_data=f"color_{color}_{size}"))
    
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="order_back_to_start"))
    
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='HTML')

def _show_image_upload(bot, chat_id: int, user_id: int):
    """Показывает экран загрузки фото"""
    text = "📷 <b>Загрузите фото</b>\n\n"
    text += "Отправьте фотографию товара, который вы хотите заказать.\n\n"
    text += "⚠️ <b>Важно:</b>\n"
    text += "• Фото должно быть четким\n"
    text += "• Показывать товар полностью\n"
    text += "• Формат: JPG, PNG"
    
    keyboard = get_back_keyboard("order_back_to_start")
    
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='HTML')

def _show_order_review(bot, chat_id: int, user_id: int):
    """Показывает предпросмотр заказа"""
    if user_id not in order_data:
        bot.send_message(chat_id, "❌ Ошибка: данные заказа не найдены")
        return
    
    data = order_data[user_id]
    
    text = "📋 <b>Предпросмотр заказа</b>\n\n"
    text += f"📏 <b>Размер:</b> {data.get('size', 'Не выбран')}\n"
    if 'color' in data and data['color'] != "_":
        text += f"🎨 <b>Цвет:</b> {data.get('color', 'Не выбран')}\n"
    text += f"📷 <b>Фото:</b> Загружено\n"
    text += f"👤 <b>Автор:</b> {role_manager.get_user_data(user_id)['first_name']}\n"
    
    from ..keyboards import get_order_review_keyboard
    keyboard = get_order_review_keyboard()
    
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='HTML')

def _show_chat_selection(bot, chat_id: int, user_id: int):
    """Показывает выбор чатов"""
    active_chats = storage.list_active_chats()
    
    if user_id not in order_data:
        order_data[user_id] = {'selected_chats': []}
    
    selected_chats = order_data[user_id].get('selected_chats', [])
    
    text = "💬 <b>Выберите чаты для отправки заказа</b>\n\n"
    text += "Отметьте чаты, в которые нужно отправить заказ:\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for chat in active_chats:
        chat_id_str = str(chat['chat_id'])
        is_selected = chat_id_str in selected_chats
        status = "✅" if is_selected else "❌"
        
        keyboard.add(InlineKeyboardButton(
            f"{status} {chat['title']} ({chat['prefix']})",
            callback_data=f"chat_toggle_{chat_id_str}"
        ))
    
    keyboard.add(
        InlineKeyboardButton("✅ Готово", callback_data="chats_selected"),
        InlineKeyboardButton("🔙 Назад", callback_data="order_back_to_start")
    )
    
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='HTML')

def _show_order_confirmation(bot, chat_id: int, user_id: int):
    """Показывает финальное подтверждение заказа"""
    if user_id not in order_data:
        bot.send_message(chat_id, "❌ Ошибка: данные заказа не найдены")
        return
    
    data = order_data[user_id]
    active_chats = storage.list_active_chats()
    selected_chats = data.get('selected_chats', [])
    
    text = "🎯 <b>Подтверждение заказа</b>\n\n"
    text += f"📏 <b>Размер:</b> {data.get('size', 'Не выбран')}\n"
    if 'color' in data and data['color'] != "_":
        text += f"🎨 <b>Цвет:</b> {data.get('color', 'Не выбран')}\n"
    text += f"📷 <b>Фото:</b> Загружено\n"
    text += f"👤 <b>Автор:</b> {role_manager.get_user_data(user_id)['first_name']}\n\n"
    
    text += "📤 <b>Чаты для отправки:</b>\n"
    for chat in active_chats:
        if str(chat['chat_id']) in selected_chats:
            text += f"• {chat['title']} ({chat['prefix']})\n"
    
    text += "\n⚠️ <b>Внимание:</b> После подтверждения заказ будет отправлен во все выбранные чаты."
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Подтвердить заказ", callback_data="order_final_confirm"),
        InlineKeyboardButton("🔙 Назад", callback_data="order_back_to_start")
    )
    
    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='HTML')

def _create_order(user_id: int) -> bool:
    """Создает заказ в системе"""
    try:
        if user_id not in order_data:
            return False
        
        data = order_data[user_id]
        size = data.get('size')
        color = data.get('color', '_')
        
        # Проверяем и резервируем остатки
        if not storage.reserve(size, color, 1):
            logger.warning(f"Не удалось зарезервировать товар: размер {size}, цвет {color}")
            return False
        
        # Создаем заказ в storage
        order_payload = {
            "user_tg_id": user_id,
            "size": size,
            "color": color,
            "photo_file_id": data.get('photo_file_id'),
            "status": "created",
            "created_at": datetime.now().isoformat()
        }
        
        order_id = storage.create_order(order_payload)
        
        # Увеличиваем счетчик заказов пользователя
        storage.inc_total_orders(user_id)
        
        # Отправляем заказ в выбранные чаты
        selected_chats = data.get('selected_chats', [])
        for chat_id_str in selected_chats:
            chat_data = storage.get_chat(chat_id_str)
            if chat_data:
                prefix = chat_data.get('prefix', '?')
                # Здесь должна быть логика отправки в чат
                # Пока что просто логируем
                logger.info(f"Заказ {order_id} должен быть отправлен в чат {chat_id_str} с префиксом {prefix}")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка создания заказа: {e}")
        # В случае ошибки освобождаем резерв
        try:
            if 'size' in locals() and 'color' in locals():
                storage.release(size, color, 1)
        except:
            pass
        return False
