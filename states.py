from telebot.handler_backends import State, StatesGroup


class SetupStates(StatesGroup):
    color = State()
    sizes = State()
    qty = State()
