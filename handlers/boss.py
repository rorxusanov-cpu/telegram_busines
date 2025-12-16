from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config import BOSS_IDS
from database.db import cursor, commit
from states.boss import BossAddAdmin, BossAddManager, BossStats
from services.statistics import get_statistics, format_statistics

router = Router()


def is_boss(tg_id: int) -> bool:
    return tg_id in BOSS_IDS


# ======================
# 👤 MENEJER QO‘SHISH
# ======================
@router.message(F.text == "👤 Menejer qo‘shish")
async def add_manager_start(message: Message, state: FSMContext):
    if not is_boss(message.from_user.id):
        return
    await state.set_state(BossAddManager.telegram_id)
    await message.answer("🆔 Menejer Telegram ID:")


@router.message(BossAddManager.telegram_id)
async def add_manager_tg(message: Message, state: FSMContext):
    await state.update_data(telegram_id=int(message.text))
    await state.set_state(BossAddManager.full_name)
    await message.answer("👤 Menejer ismi:")


@router.message(BossAddManager.full_name)
async def add_manager_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    cursor.execute("""
        INSERT INTO users (telegram_id, full_name, role)
        VALUES (?, ?, 'manager')
    """, (data["telegram_id"], message.text))
    commit()
    await message.answer("✅ Menejer qo‘shildi")
    await state.clear()


# ======================
# 👤 ADMIN QO‘SHISH
# ======================
@router.message(F.text == "👤 Admin qo‘shish")
async def add_admin_start(message: Message, state: FSMContext):
    if not is_boss(message.from_user.id):
        return
    await state.set_state(BossAddAdmin.telegram_id)
    await message.answer("🆔 Admin Telegram ID:")


@router.message(BossAddAdmin.telegram_id)
async def add_admin_tg(message: Message, state: FSMContext):
    await state.update_data(telegram_id=int(message.text))
    await state.set_state(BossAddAdmin.full_name)
    await message.answer("👤 Admin ismi:")


@router.message(BossAddAdmin.full_name)
async def add_admin_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(BossAddAdmin.manager_id)
    await message.answer("🧑‍💼 Menejer ID:")


@router.message(BossAddAdmin.manager_id)
async def add_admin_finish(message: Message, state: FSMContext):
    data = await state.get_data()

    cursor.execute("""
        INSERT INTO users (telegram_id, full_name, role, parent_id)
        VALUES (?, ?, 'admin', ?)
    """, (
        data["telegram_id"],
        data["full_name"],
        int(message.text)
    ))
    commit()

    await message.answer("✅ Admin qo‘shildi")
    await state.clear()


# ======================
# 📊 STATISTIKA (BOSS)
# ======================
@router.message(F.text == "📈 Statistika")
async def boss_stats_start(message: Message, state: FSMContext):
    if not is_boss(message.from_user.id):
        return
    await state.set_state(BossStats.date_from)
    await message.answer("📅 Boshlanish sana:")


@router.message(BossStats.date_from)
async def boss_stats_from(message: Message, state: FSMContext):
    await state.update_data(date_from=message.text)
    await state.set_state(BossStats.date_to)
    await message.answer("📅 Tugash sana:")


@router.message(BossStats.date_to)
async def boss_stats_finish(message: Message, state: FSMContext):
    data = await state.get_data()

    cursor.execute("SELECT id FROM users")
    user_ids = [r[0] for r in cursor.fetchall()]

    stats = get_statistics(user_ids, data["date_from"], message.text)
    await message.answer(format_statistics(stats, data["date_from"], message.text))
    await state.clear()
