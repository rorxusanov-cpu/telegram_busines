from aiogram.fsm.state import StatesGroup, State

class ChangeRequest(StatesGroup):
    transaction_id = State()
    new_amount = State()
    currency = State()
    source = State()
    comment = State()
