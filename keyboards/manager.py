from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def manager_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💸 Adminlarga pul berish")],
            [KeyboardButton(text="➖ Chiqim qilish")],
            [KeyboardButton(text="📄 PDF hisobot")],
            [KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="🔍 Audit")],
            [KeyboardButton(text="👥 Adminlar balansi")],
            [KeyboardButton(text="📊 Excel hisobot")],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True
    )
