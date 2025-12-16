from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.db import cursor, commit
from services.audit import log_action
from services.notify import notify_boss
from states.expense import AdminExpense
from keyboards.admin import admin_menu
from config import EXPENSE_LIMIT

router = Router()


def get_admin(tg_id: int):
    cursor.execute(
        """
        SELECT id, balance, full_name
        FROM users
        WHERE telegram_id=? AND role='admin'
        """,
        (tg_id,)
    )
    return cursor.fetchone()


# ==============================
# ➖ ADMIN → CHIQIM
# ==============================

@router.message(F.text == "➖ Chiqim qilish")
async def start_expense(message: Message, state: FSMContext):
    admin = get_admin(message.from_user.id)
    if not admin:
        return

    await state.set_state(AdminExpense.amount)
    await message.answer("💸 Summani kiriting:")


@router.message(AdminExpense.amount)
async def expense_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("❌ Noto‘g‘ri summa")
        return

    await state.update_data(amount=amount)
    await state.set_state(AdminExpense.currency)
    await message.answer("💱 Valyuta (UZS / USD):")


@router.message(AdminExpense.currency)
async def expense_currency(message: Message, state: FSMContext):
    await state.update_data(currency=message.text.upper())
    await state.set_state(AdminExpense.source)
    await message.answer("💳 Manba (karta / naqd):")


@router.message(AdminExpense.source)
async def expense_source(message: Message, state: FSMContext):
    await state.update_data(source=message.text.lower())
    await state.set_state(AdminExpense.comment)
    await message.answer("✍️ Izoh:")


@router.message(AdminExpense.comment)
async def expense_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    admin = get_admin(message.from_user.id)

    if not admin:
        await state.clear()
        return

    admin_id, balance, admin_name = admin
    amount = data["amount"]

    if balance < amount:
        await message.answer("❌ Balans yetarli emas")
        await state.clear()
        return

    cursor.execute(
        """
        INSERT INTO transactions
        (user_id, amount, currency, source, type, comment)
        VALUES (?, ?, ?, ?, 'expense', ?)
        """,
        (
            admin_id,
            amount,
            data["currency"],
            data["source"],
            message.text
        )
    )

    cursor.execute(
        "UPDATE users SET balance = balance - ? WHERE id=?",
        (amount, admin_id)
    )

    commit()

    log_action(
        actor_id=admin_id,
        action="ADMIN_EXPENSE",
        details=f"{amount} {data['currency']} | {data['source']} | {message.text}"
    )

    if amount >= EXPENSE_LIMIT:
        await notify_boss(
            f"🚨 KATTA CHIQIM\n"
            f"Admin: {admin_name}\n"
            f"Summa: {amount} {data['currency']}"
        )

    await message.answer("✅ Chiqim saqlandi", reply_markup=admin_menu())
    await state.clear()
