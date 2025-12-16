from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from config import BOSS_IDS
from database.db import cursor
from keyboards.boss import boss_menu
from keyboards.manager import manager_menu
from keyboards.admin import admin_menu

router = Router()


@router.message(Command("start"))
async def start_cmd(message: Message):
    user_id = message.from_user.id

    if user_id in BOSS_IDS:
        await message.answer("👑 Boss panel", reply_markup=boss_menu())
        return

    cursor.execute(
        "SELECT role FROM users WHERE telegram_id=?",
        (user_id,)
    )
    row = cursor.fetchone()

    if not row:
        await message.answer("❌ Siz tizimda yo‘qsiz")
        return

    if row[0] == "manager":
        await message.answer("👤 Menejer panel", reply_markup=manager_menu())
    elif row[0] == "admin":
        await message.answer("🛡 Admin panel", reply_markup=admin_menu())
