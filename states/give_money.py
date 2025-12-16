from aiogram.fsm.state import StatesGroup, State

class GiveMoney(StatesGroup):
    admin = State()
    amount = State()
    currency = State()
    source = State()
    comment = State()
