from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.db import cursor, commit
from config import EXPENSE_LIMIT
from services.notify import notify_boss
from services.audit import log_action

from states.expense import AdminExpense, AdminIncome

router = Router()

# ---------- HELPERS ----------
def get_admin(telegram_id: int):
    cursor.execute(
        "SELECT id, parent_id, full_name FROM users "
        "WHERE telegram_id=? AND role='admin'",
        (telegram_id,)
    )
    return cursor.fetchone()

# =============================
#        ADMIN EXPENSE
# =============================

@router.message(F.text == "➖ Chiqim qilish")
async def start_expense(message: Message, state: FSMContext):
    if not get_admin(message.from_user.id):
        return
    await state.set_state(AdminExpense.amount)
    await message.answer("💸 Summani kiriting:")

@router.message(AdminExpense.amount)
async def expense_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("❌ Faqat raqam kiriting")
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
    await message.answer("💳 Manba (karta / naqd):")

@router.message(AdminExpense.source)
async def expense_source(message: Message, state: FSMContext):
    source = message.text.lower()
    if source not in ("karta", "naqd"):
        await message.answer("❌ Faqat karta yoki naqd")
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

    data = await state.get_data()
    amount = data["amount"]
    currency = data["currency"]
    source = data["source"]
    comment = message.text

    admin_id, manager_id, admin_name = admin

    # DB
    cursor.execute("""
        INSERT INTO transactions
        (user_id, amount, currency, source, type, comment)
        VALUES (?, ?, ?, ?, 'expense', ?)
    """, (admin_id, amount, currency, source, comment))

    cursor.execute("UPDATE users SET balance = balance - ? WHERE id=?", (amount, admin_id))
    cursor.execute("UPDATE users SET balance = balance - ? WHERE id=?", (amount, manager_id))
    commit()

    # Audit
    log_action(
        actor_id=admin_id,
        action="ADMIN_EXPENSE",
        details=f"{amount} {currency} | {source} | {comment}"
    )

    # Limit → boss
    if amount > EXPENSE_LIMIT:
        await notify_boss(
            f"🚨 KATTA CHIQIM\n"
            f"Admin: {admin_name}\n"
            f"{amount} {currency}\n"
            f"{source}\n"
            f"{comment}"
        )

    await message.answer("✅ Chiqim saqlandi")
    await state.clear()

# =============================
#        ADMIN INCOME
# =============================

@router.message(F.text == "➕ Kirim kiritish")
async def start_income(message: Message, state: FSMContext):
    if not get_admin(message.from_user.id):
        return
    await state.set_state(AdminIncome.amount)
    await message.answer("💰 Summani kiriting:")

@router.message(AdminIncome.amount)
async def income_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("❌ Faqat raqam kiriting")
        return

    await state.update_data(amount=amount)
    await state.set_state(AdminIncome.currency)
    await message.answer("💱 Valyuta (UZS / USD):")

@router.message(AdminIncome.currency)
async def income_currency(message: Message, state: FSMContext):
    currency = message.text.upper()
    if currency not in ("UZS", "USD"):
        await message.answer("❌ Faqat UZS yoki USD")
        return

    await state.update_data(currency=currency)
    await state.set_state(AdminIncome.source)
    await message.answer("💳 Manba (karta / naqd):")

@router.message(AdminIncome.source)
async def income_source(message: Message, state: FSMContext):
    source = message.text.lower()
    if source not in ("karta", "naqd"):
        await message.answer("❌ Faqat karta yoki naqd")
        return

    await state.update_data(source=source)
    await state.set_state(AdminIncome.comment)
    await message.answer("✍️ Izoh:")

@router.message(AdminIncome.comment)
async def income_finish(message: Message, state: FSMContext):
    admin = get_admin(message.from_user.id)
    if not admin:
        await state.clear()
        return

    data = await state.get_data()
    amount = data["amount"]
    currency = data["currency"]
    source = data["source"]
    comment = message.text

    admin_id, manager_id, _ = admin

    cursor.execute("""
        INSERT INTO transactions
        (user_id, amount, currency, source, type, comment)
        VALUES (?, ?, ?, ?, 'income', ?)
    """, (admin_id, amount, currency, source, comment))

    cursor.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, admin_id))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, manager_id))
    commit()

    log_action(
        actor_id=admin_id,
        action="ADMIN_INCOME",
        details=f"{amount} {currency} | {source} | {comment}"
    )

    await message.answer("✅ Kirim saqlandi")
    await state.clear()
