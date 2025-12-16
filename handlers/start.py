from aiogram import Router
from aiogram.types import Message

from database.db import cursor, commit
from config import BOSS_IDS

from keyboards.boss import boss_menu
from keyboards.manager import manager_menu
from keyboards.admin import admin_menu

router = Router()


@router.message()
async def start_handler(message: Message):
    if message.text != "/start":
        return

    tg_id = message.from_user.id
    full_name = message.from_user.full_name

    # 👑 Boss
    if tg_id in BOSS_IDS:
        await message.answer(
            f"👑 Xush kelibsiz, Boss {full_name}",
            reply_markup=boss_menu()
        )
        return

    # DB da bormi?
    cursor.execute(
        "SELECT role FROM users WHERE telegram_id=?",
        (tg_id,)
    )
    user = cursor.fetchone()

    # ❗ Agar DB da yo‘q bo‘lsa — hozircha hech narsa qilmaymiz
    if not user:
        await message.answer(
            "❌ Siz tizimga biriktirilmagansiz.\n"
            "Administrator bilan bog‘laning."
        )
        return

    role = user[0]

    # 👤 Manager
    if role == "manager":
        await message.answer(
            f"👤 Xush kelibsiz, Menejer {full_name}",
            reply_markup=manager_menu()
        )
        return

    # 👤 Admin
    if role == "admin":
        await message.answer(
            f"👤 Xush kelibsiz, Admin {full_name}",
            reply_markup=admin_menu()
        )
        return

    # fallback
    await message.answer("❌ Rol aniqlanmadi")
