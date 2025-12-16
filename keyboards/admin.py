from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➖ Chiqim qilish")],
            [KeyboardButton(text="📄 Hisobot")],
            [KeyboardButton(text="💰 Balansim")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )
