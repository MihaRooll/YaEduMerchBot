from telebot import TeleBot

from services.inventory import add_item
from services.settings import is_configured, set_configured
from states import SetupStates


def register_handlers(bot: TeleBot) -> None:
    @bot.message_handler(commands=["start"])
    def start(message):
        if not is_configured():
            bot.send_message(message.chat.id, "Введите цвет мерча:")
            bot.set_state(message.from_user.id, SetupStates.color, message.chat.id)
        else:
            bot.send_message(message.chat.id, "Бот готов к работе.")

    @bot.message_handler(state=SetupStates.color)
    def setup_color(message):
        bot.storage.set_data(
            message.from_user.id, message.chat.id, {"color": message.text.strip()}
        )
        bot.send_message(message.chat.id, "Введите размеры через запятую:")
        bot.set_state(message.from_user.id, SetupStates.sizes, message.chat.id)

    @bot.message_handler(state=SetupStates.sizes)
    def setup_sizes(message):
        sizes = [s.strip() for s in message.text.split(",") if s.strip()]
        data = bot.storage.get_data(message.from_user.id, message.chat.id) or {}
        data["sizes"] = sizes
        data["index"] = 0
        bot.storage.set_data(message.from_user.id, message.chat.id, data)
        bot.send_message(message.chat.id, f"Введите количество для размера {sizes[0]}:")
        bot.set_state(message.from_user.id, SetupStates.qty, message.chat.id)

    @bot.message_handler(state=SetupStates.qty)
    def setup_qty(message):
        data = bot.storage.get_data(message.from_user.id, message.chat.id) or {}
        sizes = data.get("sizes", [])
        index = data.get("index", 0)
        try:
            qty = int(message.text.strip())
        except ValueError:
            bot.send_message(message.chat.id, "Введите число.")
            return
        add_item(sizes[index], data["color"], qty)
        index += 1
        if index < len(sizes):
            data["index"] = index
            bot.storage.set_data(message.from_user.id, message.chat.id, data)
            bot.send_message(
                message.chat.id, f"Введите количество для размера {sizes[index]}:"
            )
        else:
            set_configured()
            bot.delete_state(message.from_user.id, message.chat.id)
            bot.send_message(message.chat.id, "Настройка завершена.")
