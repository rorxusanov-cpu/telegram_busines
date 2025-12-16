from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➖ Chiqim qilish")],
            [KeyboardButton(text="➕ Kirim kiritish")],
            [KeyboardButton(text="✏️ O‘zgartirish so‘rovi")],
            [KeyboardButton(text="📄 PDF hisobot")],
            [KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="📊 Excel hisobot")],
            [KeyboardButton(text="💰 Balansim")],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True
    )
