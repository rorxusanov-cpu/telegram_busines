from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.db import cursor, commit
from config import EXPENSE_LIMIT
from services.notify import notify_boss
from services.audit import log_action
from services.pdf import generate_pdf
from services.statistics import get_statistics, format_statistics
from services.audit_view import get_audit, format_audit
from services.excel import generate_excel

from states.expense import AdminExpense
from states.change import ChangeRequest
from states.boss import BossPDF, BossStats
from states.audit import AuditState

from aiogram.types import FSInputFile

router = Router()

# ---------- HELPERS ----------
def get_admin(telegram_id: int):
    cursor.execute(
        "SELECT id, balance, parent_id, full_name FROM users "
        "WHERE telegram_id=? AND role='admin'",
        (telegram_id,)
    )
    return cursor.fetchone()

# =============================
#        ADMIN CHIQIM (FSM)
# =============================

@router.message(F.text == "➖ Chiqim qilish")
async def start_expense(message: Message, state: FSMContext):
    if not get_admin(message.from_user.id):
        return
    await state.set_state(AdminExpense.amount)
    await message.answer("💸 Summani kiriting:")

@router.message(AdminExpense.amount)
async def expense_amount(message: Message, state: FSMContext):
    await state.update_data(amount=float(message.text))
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
    admin = get_admin(message.from_user.id)
    if not admin:
        return

    data = await state.get_data()
    amount = data["amount"]
    currency = data["currency"]
    source = data["source"]
    comment = message.text

    admin_id, _, manager_id, full_name = admin

    cursor.execute("""
        INSERT INTO transactions
        (user_id, amount, currency, source, type, comment)
        VALUES (?, ?, ?, ?, 'expense', ?)
    """, (admin_id, amount, currency, source, comment))

    cursor.execute("UPDATE users SET balance = balance - ? WHERE id=?", (amount, admin_id))
    cursor.execute("UPDATE users SET balance = balance - ? WHERE id=?", (amount, manager_id))
    commit()

    log_action(
        actor_id=admin_id,
        action="ADMIN_EXPENSE",
        details=f"{amount} {currency} | {source} | {comment}"
    )

    if amount > EXPENSE_LIMIT:
        await notify_boss(
            f"🚨 KATTA CHIQIM\nAdmin: {full_name}\n"
            f"{amount} {currency}\n{source}\n{comment}"
        )

    await message.answer("✅ Chiqim saqlandi")
    await state.clear()

# =============================
#        ADMIN BALANS
# =============================

@router.message(F.text == "💰 Balansim")
async def admin_balance(message: Message):
    admin = get_admin(message.from_user.id)
    if not admin:
        return

    _, balance, _, _ = admin
    await message.answer(f"💰 Balansingiz:\n{balance:,.0f}")

# =============================
#        PDF
# =============================

@router.message(F.text == "📄 PDF hisobot")
async def admin_pdf_start(message: Message, state: FSMContext):
    await state.set_state(BossPDF.date_from)
    await message.answer("📅 Boshlanish sana (YYYY-MM-DD):")

@router.message(BossPDF.date_from)
async def admin_pdf_from(message: Message, state: FSMContext):
    await state.update_data(date_from=message.text)
    await state.set_state(BossPDF.date_to)
    await message.answer("📅 Tugash sana (YYYY-MM-DD):")

@router.message(BossPDF.date_to)
async def admin_pdf_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    admin = get_admin(message.from_user.id)

    file_path = generate_pdf(
        [admin[0]],
        data["date_from"],
        message.text,
        f"admin_{admin[0]}.pdf"
    )

    await message.answer_document(FSInputFile(file_path))
    await state.clear()

# =============================
#        STATISTIKA
# =============================

@router.message(F.text == "📊 Statistika")
async def admin_stats_start(message: Message, state: FSMContext):
    await state.set_state(BossStats.date_from)
    await message.answer("📅 Boshlanish sana:")

@router.message(BossStats.date_to)
async def admin_stats_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    admin = get_admin(message.from_user.id)

    stats = get_statistics([admin[0]], data["date_from"], message.text)
    await message.answer(format_statistics(stats, data["date_from"], message.text))
    await state.clear()

# =============================
#        AUDIT
# =============================

@router.message(F.text == "🔍 Audit")
async def admin_audit_start(message: Message, state: FSMContext):
    await state.set_state(AuditState.date_from)
    await message.answer("📅 Boshlanish sana:")

@router.message(AuditState.date_to)
async def admin_audit_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    admin = get_admin(message.from_user.id)

    rows = get_audit([admin[0]], data["date_from"], message.text)
    await message.answer(format_audit(rows, data["date_from"], message.text))
    await state.clear()

# =============================
#        EXCEL
# =============================

@router.message(F.text == "📊 Excel hisobot")
async def admin_excel_start(message: Message, state: FSMContext):
    await state.set_state(BossPDF.date_from)
    await message.answer("📅 Boshlanish sana:")

@router.message(BossPDF.date_to)
async def admin_excel_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    admin = get_admin(message.from_user.id)

    path = generate_excel(
        [admin[0]],
        data["date_from"],
        message.text,
        f"admin_{admin[0]}.xlsx"
    )

    await message.answer_document(FSInputFile(path))
    await state.clear()
