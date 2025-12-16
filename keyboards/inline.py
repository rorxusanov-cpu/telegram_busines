from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def approve_kb(request_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=f"approve:{request_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Rad etish",
                    callback_data=f"reject:{request_id}"
                )
            ]
        ]
    )
