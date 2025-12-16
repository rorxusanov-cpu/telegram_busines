from aiogram.fsm.state import StatesGroup, State

class BossGiveMoney(StatesGroup):
    manager_id = State()
    amount = State()
    currency = State()
    source = State()
    comment = State()


class BossPDF(StatesGroup):
    date_from = State()
    date_to = State()


class BossStats(StatesGroup):
    date_from = State()
    date_to = State()


class BossAudit(StatesGroup):
    date_from = State()
    date_to = State()
