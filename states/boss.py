from aiogram.fsm.state import StatesGroup, State


class BossAddManager(StatesGroup):
    telegram_id = State()
    full_name = State()


class BossAddAdmin(StatesGroup):
    telegram_id = State()
    full_name = State()
    manager_id = State()


class BossStats(StatesGroup):
    date_from = State()
    date_to = State()
