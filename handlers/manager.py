from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext

from database.db import cursor, commit
from services.notify import notify_boss
from services.audit import log_action
from services.pdf import generate_pdf
from services.statistics import get_statistics, format_statistics
from services.audit_view import get_audit, format_audit
from services.excel import generate_excel

from states.give_money import GiveMoney
from states.boss import BossPDF, BossStats
from states.audit import AuditState

router = Router()

# ---------- HELPERS ----------
def get_manager(telegram_id: int):
    cursor.execute(
        "SELECT id, balance, full_name FROM users "
        "WHERE telegram_id=? AND role='manager'",
        (telegram_id,)
    )
    return cursor.fetchone()


def get_admins(manager_id: int):
    cursor.execute(
        "SELECT id, full_name FROM users "
        "WHERE parent_id=? AND role='admin'",
        (manager_id,)
    )
    return cursor.fetchall()

# =============================
# 💸 MANAGER → ADMIN PUL
# =============================

@router.message(F.text == "💸 Adminlarga pul berish")
async def start_give(message: Message, state: FSMContext):
    if not get_manager(message.from_user.id):
        return
    await state.set_state(GiveMoney.admin)
    await message.answer("🆔 Admin ID kiriting:")

@router.message(GiveMoney.admin)
async def give_admin(message: Message, state: FSMContext):
    await state.update_data(admin_id=int(message.text))
    await state.set_state(GiveMoney.amount)
    await message.answer("💸 Summa:")

@router.message(GiveMoney.amount)
async def give_amount(message: Message, state: FSMContext):
    await state.update_data(amount=float(message.text))
    await state.set_state(GiveMoney.currency)
    await message.answer("💱 Valyuta (UZS / USD):")

@router.message(GiveMoney.currency)
async def give_currency(message: Message, state: FSMContext):
    await state.update_data(currency=message.text.upper())
    await state.set_state(GiveMoney.source)
    await message.answer("💳 Manba (karta / naqd):")

@router.message(GiveMoney.source)
async def give_source(message: Message, state: FSMContext):
    await state.update_data(source=message.text.lower())
    await state.set_state(GiveMoney.comment)
    await message.answer("✍️ Izoh:")

@router.message(GiveMoney.comment)
async def give_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    manager = get_manager(message.from_user.id)
    if not manager:
        await state.clear()
        return

    manager_id, manager_balance, manager_name = manager
    admin_id = data["admin_id"]
    amount = data["amount"]
    currency = data["currency"]
    source = data["source"]
    comment = message.text

    if manager_balance < amount:
        await message.answer("❌ Balans yetarli emas")
        await state.clear()
        return

    cursor.execute(
        "SELECT full_name FROM users "
        "WHERE id=? AND parent_id=? AND role='admin'",
        (admin_id, manager_id)
    )
    admin = cursor.fetchone()
    if not admin:
        await message.answer("❌ Admin topilmadi")
        await state.clear()
        return

    admin_name = admin[0]

    cursor.execute("""
        INSERT INTO transactions
        (user_id, amount, currency, source, type, comment)
        VALUES (?, ?, ?, ?, 'income', ?)
    """, (admin_id, amount, currency, source, comment))

    cursor.execute("UPDATE users SET balance = balance - ? WHERE id=?", (amount, manager_id))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, admin_id))
    commit()

    log_action(
        actor_id=manager_id,
        action="MANAGER_GIVE_ADMIN",
        details=f"{admin_name} ← {amount} {currency} | {source} | {comment}"
    )

    await notify_boss(
        f"💸 MENEJER ADMINIGA PUL AJRATDI\n"
        f"Menejer: {manager_name}\n"
        f"Admin: {admin_name}\n"
        f"{amount} {currency}\n{source}\n{comment}"
    )

    await message.answer("✅ Pul ajratildi")
    await state.clear()

# =============================
# 👥 ADMINLAR BALANSI
# =============================

@router.message(F.text == "👥 Adminlar balansi")
async def admins_balance(message: Message):
    manager = get_manager(message.from_user.id)
    if not manager:
        return

    manager_id, _, _ = manager

    cursor.execute(
        "SELECT full_name, balance FROM users "
        "WHERE parent_id=? AND role='admin'",
        (manager_id,)
    )
    admins = cursor.fetchall()

    if not admins:
        await message.answer("📭 Adminlar yo‘q")
        return

    text = "👥 Adminlar balansi\n\n"
    for name, balance in admins:
        text += f"👤 {name}\n💰 {balance:,.0f}\n\n"

    await message.answer(text)

# =============================
# 📄 PDF HISOBOT
# =============================

@router.message(F.text == "📄 PDF hisobot")
async def manager_pdf_start(message: Message, state: FSMContext):
    await state.set_state(BossPDF.date_from)
    await message.answer("📅 Boshlanish sana:")

@router.message(BossPDF.date_to)
async def manager_pdf_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    manager = get_manager(message.from_user.id)
    manager_id = manager[0]

    cursor.execute(
        "SELECT id FROM users WHERE parent_id=? AND role='admin'",
        (manager_id,)
    )
    admin_ids = [r[0] for r in cursor.fetchall()]
    user_ids = admin_ids + [manager_id]

    path = generate_pdf(user_ids, data["date_from"], message.text, f"manager_{manager_id}.pdf")
    await message.answer_document(FSInputFile(path))
    await state.clear()

# =============================
# 📊 STATISTIKA
# =============================

@router.message(F.text == "📊 Statistika")
async def manager_stats_start(message: Message, state: FSMContext):
    await state.set_state(BossStats.date_from)
    await message.answer("📅 Boshlanish sana:")

@router.message(BossStats.date_to)
async def manager_stats_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    manager = get_manager(message.from_user.id)
    manager_id = manager[0]

    cursor.execute(
        "SELECT id FROM users WHERE parent_id=? AND role='admin'",
        (manager_id,)
    )
    admin_ids = [r[0] for r in cursor.fetchall()]
    user_ids = admin_ids + [manager_id]

    stats = get_statistics(user_ids, data["date_from"], message.text)
    await message.answer(format_statistics(stats, data["date_from"], message.text))
    await state.clear()

# =============================
# 🔍 AUDIT
# =============================

@router.message(F.text == "🔍 Audit")
async def manager_audit_start(message: Message, state: FSMContext):
    await state.set_state(AuditState.date_from)
    await message.answer("📅 Boshlanish sana:")

@router.message(AuditState.date_to)
async def manager_audit_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    manager = get_manager(message.from_user.id)
    manager_id = manager[0]

    cursor.execute(
        "SELECT id FROM users WHERE parent_id=?",
        (manager_id,)
    )
    user_ids = [r[0] for r in cursor.fetchall()] + [manager_id]

    rows = get_audit(user_ids, data["date_from"], message.text)
    await message.answer(format_audit(rows, data["date_from"], message.text))
    await state.clear()

# =============================
# 📊 EXCEL
# =============================

@router.message(F.text == "📊 Excel hisobot")
async def manager_excel_start(message: Message, state: FSMContext):
    await state.set_state(BossPDF.date_from)
    await message.answer("📅 Boshlanish sana:")

@router.message(BossPDF.date_to)
async def manager_excel_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    manager = get_manager(message.from_user.id)
    manager_id = manager[0]

    cursor.execute(
        "SELECT id FROM users WHERE parent_id=? AND role='admin'",
        (manager_id,)
    )
    admin_ids = [r[0] for r in cursor.fetchall()]
    user_ids = admin_ids + [manager_id]

    path = generate_excel(user_ids, data["date_from"], message.text, f"manager_{manager_id}.xlsx")
    await message.answer_document(FSInputFile(path))
    await state.clear()
