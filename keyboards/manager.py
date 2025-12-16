from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def manager_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💸 Adminlarga pul berish")],
            [KeyboardButton(text="📄 Hisobot")],
            [KeyboardButton(text="👥 Adminlar balansi")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )
