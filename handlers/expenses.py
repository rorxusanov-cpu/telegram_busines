from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.db import cursor, commit
from services.notify import notify_boss
from services.audit import log_action
from states.expense import AdminExpense
from config import EXPENSE_LIMIT

router = Router()


# ---------- HELPERS ----------
def get_admin(tg_id: int):
    cursor.execute(
        """
        SELECT id, balance, parent_id, full_name
        FROM users
        WHERE telegram_id=? AND role='admin'
        """,
        (tg_id,)
    )
    return cursor.fetchone()


# ==============================
# ➖ ADMIN → CHIQIM (FSM)
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
    currency = message.text.upper()
    if currency not in ("UZS", "USD"):
        await message.answer("❌ Faqat UZS yoki USD")
        return

    await state.update_data(currency=currency)
    await state.set_state(AdminExpense.source)
    await message.answer("💳 Manba (card / cash):")


@router.message(AdminExpense.source)
async def expense_source(message: Message, state: FSMContext):
    source = message.text.lower()
    if source not in ("card", "cash"):
        await message.answer("❌ card yoki cash")
        return

    await state.update_data(source=source)
    await state.set_state(AdminExpense.comment)
    await message.answer("✍️ Izoh:")


@router.message(AdminExpense.comment)
async def expense_finish(message: Message, state: FSMContext):
    admin = get_admin(message.from_user.id)
    if not admin:
        await state.clear()
        return

    admin_id, admin_balance, manager_id, admin_name = admin
    data = await state.get_data()

    amount = data["amount"]
    currency = data["currency"]
    source = data["source"]
    comment = message.text

    if admin_balance < amount:
        await message.answer("❌ Balans yetarli emas")
        await state.clear()
        return

    # ---- TRANSACTION ----
    cursor.execute("""
        INSERT INTO transactions
        (user_id, amount, currency, source, type, comment)
        VALUES (?, ?, ?, ?, 'expense', ?)
    """, (admin_id, amount, currency, source, comment))

    # ---- BALANCE ----
    cursor.execute(
        "UPDATE users SET balance = balance - ? WHERE id=?",
        (amount, admin_id)
    )
    cursor.execute(
        "UPDATE users SET balance = balance - ? WHERE id=?",
        (amount, manager_id)
    )

    commit()

    # ---- AUDIT ----
    log_action(
        actor_id=admin_id,
        action="ADMIN_EXPENSE",
        details=f"{amount} {currency} | {source} | {comment}"
    )

    # ---- BOSS NOTIFY ----
    if amount >= EXPENSE_LIMIT:
        await notify_boss(
            f"🚨 KATTA CHIQIM\n\n"
            f"Admin: {admin_name}\n"
            f"Summa: {amount} {currency}\n"
            f"Manba: {source}\n"
            f"Izoh: {comment}"
        )

    await message.answer("✅ Chiqim saqlandi")
    await state.clear()
