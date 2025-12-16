from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext

from database.db import cursor, commit
from config import BOSS_IDS

from services.audit import log_action
from services.pdf import generate_pdf
from services.statistics import get_statistics, format_statistics
from services.audit_view import get_audit, format_audit
from services.excel import generate_excel

from states.boss import BossGiveMoney, BossPDF, BossStats, BossAudit

router = Router()

# ---------- HELPERS ----------
def is_boss(tg_id: int) -> bool:
    return tg_id in BOSS_IDS


def get_manager(manager_id: int):
    cursor.execute(
        "SELECT id, full_name FROM users WHERE id=? AND role='manager'",
        (manager_id,)
    )
    return cursor.fetchone()


# ==============================
# 💸 BOSS → MENEJERGA PUL
# ==============================

@router.message(F.text == "💸 Pul tarqatish")
async def boss_give_start(message: Message, state: FSMContext):
    if not is_boss(message.from_user.id):
        return
    await state.set_state(BossGiveMoney.manager_id)
    await message.answer("👤 Menejer ID kiriting:")


@router.message(BossGiveMoney.manager_id)
async def boss_give_manager(message: Message, state: FSMContext):
    await state.update_data(manager_id=int(message.text))
    await state.set_state(BossGiveMoney.amount)
    await message.answer("💸 Summa:")


@router.message(BossGiveMoney.amount)
async def boss_give_amount(message: Message, state: FSMContext):
    await state.update_data(amount=float(message.text))
    await state.set_state(BossGiveMoney.currency)
    await message.answer("💱 Valyuta (UZS / USD):")


@router.message(BossGiveMoney.currency)
async def boss_give_currency(message: Message, state: FSMContext):
    await state.update_data(currency=message.text.upper())
    await state.set_state(BossGiveMoney.source)
    await message.answer("💳 Manba (karta / naqd):")


@router.message(BossGiveMoney.source)
async def boss_give_source(message: Message, state: FSMContext):
    await state.update_data(source=message.text.lower())
    await state.set_state(BossGiveMoney.comment)
    await message.answer("✍️ Izoh:")


@router.message(BossGiveMoney.comment)
async def boss_give_finish(message: Message, state: FSMContext):
    data = await state.get_data()

    manager = get_manager(data["manager_id"])
    if not manager:
        await message.answer("❌ Menejer topilmadi")
        await state.clear()
        return

    manager_id, manager_name = manager
    amount = data["amount"]
    currency = data["currency"]
    source = data["source"]
    comment = message.text

    cursor.execute(
        "UPDATE users SET balance = balance + ? WHERE id=?",
        (amount, manager_id)
    )

    cursor.execute("""
        INSERT INTO transactions
        (user_id, amount, currency, source, type, comment)
        VALUES (?, ?, ?, ?, 'income', ?)
    """, (manager_id, amount, currency, source, comment))

    commit()

    log_action(
        actor_id=manager_id,
        action="BOSS_GIVE_MANAGER",
        details=f"{amount} {currency} | {source} | {comment}"
    )

    await message.answer("✅ Pul ajratildi")
    await state.clear()

# ==============================
# 📄 BOSS → UMUMIY PDF
# ==============================

@router.message(F.text == "📊 Umumiy PDF")
async def boss_pdf_start(message: Message, state: FSMContext):
    if not is_boss(message.from_user.id):
        return
    await state.set_state(BossPDF.date_from)
    await message.answer("📅 Boshlanish sana (YYYY-MM-DD):")


@router.message(BossPDF.date_from)
async def boss_pdf_from(message: Message, state: FSMContext):
    await state.update_data(date_from=message.text)
    await state.set_state(BossPDF.date_to)
    await message.answer("📅 Tugash sana (YYYY-MM-DD):")


@router.message(BossPDF.date_to)
async def boss_pdf_finish(message: Message, state: FSMContext):
    data = await state.get_data()

    cursor.execute("SELECT id FROM users")
    user_ids = [r[0] for r in cursor.fetchall()]

    path = generate_pdf(
        user_ids,
        data["date_from"],
        message.text,
        "boss_all.pdf"
    )

    await message.answer_document(FSInputFile(path))
    await state.clear()

# ==============================
# 📈 BOSS → STATISTIKA
# ==============================

@router.message(F.text == "📈 Statistika")
async def boss_stats_start(message: Message, state: FSMContext):
    if not is_boss(message.from_user.id):
        return
    await state.set_state(BossStats.date_from)
    await message.answer("📅 Boshlanish sana:")


@router.message(BossStats.date_to)
async def boss_stats_finish(message: Message, state: FSMContext):
    data = await state.get_data()

    cursor.execute("SELECT id FROM users")
    user_ids = [r[0] for r in cursor.fetchall()]

    stats = get_statistics(user_ids, data["date_from"], message.text)
    await message.answer(format_statistics(stats, data["date_from"], message.text))
    await state.clear()

# ==============================
# 🔍 BOSS → AUDIT
# ==============================

@router.message(F.text == "🔍 Audit")
async def boss_audit_start(message: Message, state: FSMContext):
    if not is_boss(message.from_user.id):
        return
    await state.set_state(BossAudit.date_from)
    await message.answer("📅 Boshlanish sana:")


@router.message(BossAudit.date_to)
async def boss_audit_finish(message: Message, state: FSMContext):
    data = await state.get_data()

    cursor.execute("SELECT id FROM users")
    user_ids = [r[0] for r in cursor.fetchall()]

    rows = get_audit(user_ids, data["date_from"], message.text)
    await message.answer(format_audit(rows, data["date_from"], message.text))
    await state.clear()

# ==============================
# 📊 BOSS → EXCEL
# ==============================

@router.message(F.text == "📊 Excel hisobot")
async def boss_excel_start(message: Message, state: FSMContext):
    if not is_boss(message.from_user.id):
        return
    await state.set_state(BossPDF.date_from)
    await message.answer("📅 Boshlanish sana:")


@router.message(BossPDF.date_to)
async def boss_excel_finish(message: Message, state: FSMContext):
    data = await state.get_data()

    cursor.execute("SELECT id FROM users")
    user_ids = [r[0] for r in cursor.fetchall()]

    path = generate_excel(
        user_ids,
        data["date_from"],
        message.text,
        "boss_all.xlsx"
    )

    await message.answer_document(FSInputFile(path))
    await state.clear()
