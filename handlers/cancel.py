from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards.boss import boss_menu
from keyboards.manager import manager_menu
from keyboards.admin import admin_menu
from config import BOSS_IDS
from database.db import cursor

router = Router()

@router.message(F.text == "❌ Bekor qilish")
async def cancel_handler(message: Message, state: FSMContext):
    # FSM bo‘lsa — tozalaymiz
    if await state.get_state():
        await state.clear()

    user_id = message.from_user.id

    # 👑 Boss
    if user_id in BOSS_IDS:
        await message.answer(
            "❌ Amal bekor qilindi",
            reply_markup=boss_menu()
        )
        return

    # 👤 Manager / Admin
    cursor.execute(
        "SELECT role FROM users WHERE telegram_id=?",
        (user_id,)
    )
    row = cursor.fetchone()

    if not row:
        await message.answer("❌ Amal bekor qilindi")
        return

    role = row[0]

    if role == "manager":
        await message.answer(
            "❌ Amal bekor qilindi",
            reply_markup=manager_menu()
        )
    elif role == "admin":
        await message.answer(
            "❌ Amal bekor qilindi",
            reply_markup=admin_menu()
        )
    else:
        await message.answer("❌ Amal bekor qilindi")
