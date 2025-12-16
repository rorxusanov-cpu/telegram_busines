from aiogram.fsm.state import StatesGroup, State

class AdminExpense(StatesGroup):
    amount = State()
    currency = State()
    source = State()
    comment = State()


class AdminIncome(StatesGroup):
    amount = State()
    currency = State()
    source = State()
    comment = State()
