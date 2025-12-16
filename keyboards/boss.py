from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def boss_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💸 Pul tarqatish")],
            [KeyboardButton(text="➕ Admin qo‘shish")],
            [KeyboardButton(text="➕ Menejer qo‘shish")],
            [KeyboardButton(text="📊 Umumiy PDF")],
            [KeyboardButton(text="📈 Statistika")],
            [KeyboardButton(text="🔍 Audit")],
            [KeyboardButton(text="📊 Excel hisobot")],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True
    )
