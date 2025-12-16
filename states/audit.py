from aiogram.fsm.state import State, StatesGroup


class AuditState(StatesGroup):
    date_from = State()
    date_to = State()
