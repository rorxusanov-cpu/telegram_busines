from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.db import cursor, commit
from services.notify import notify_boss
from services.audit import log_action
from services.pdf import generate_pdf
from services.excel import generate_excel

from states.give_money import GiveMoney
from states.boss import BossPDF

from aiogram.types import FSInputFile

router = Router()

# =========================
# HELPERS
# =========================

def get_manager(tg_id: int):
    cursor.execute(
        """
        SELECT id, full_name, balance
        FROM users
        WHERE telegram_id=? AND role='manager'
        """,
        (tg_id,)
    )
    return cursor.fetchone()


def get_admin(manager_id: int, admin_id: int):
    cursor.execute(
        """
        SELECT id, full_name
        FROM users
        WHERE id=? AND parent_id=? AND role='admin'
        """,
        (admin_id, manager_id)
    )
    return cursor.fetchone()


# =========================
# 💸 MANAGER → ADMIN PUL
# =========================

@router.message(F.text == "💸 Adminlarga pul berish")
async def give_start(message: Message, state: FSMContext):
    manager = get_manager(message.from_user.id)
    if not manager:
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

    manager_id, manager_name, manager_balance = manager
    admin = get_admin(manager_id, data["admin_id"])

    if not admin:
        await message.answer("❌ Admin topilmadi")
        await state.clear()
        return

    admin_id, admin_name = admin
    amount = data["amount"]

    if manager_balance < amount:
        await message.answer("❌ Balans yetarli emas")
        await state.clear()
        return

    # Balanslar
    cursor.execute("UPDATE users SET balance = balance - ? WHERE id=?", (amount, manager_id))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, admin_id))

    # Transaction
    cursor.execute("""
        INSERT INTO transactions (user_id, amount, currency, source, type, comment)
        VALUES (?, ?, ?, ?, 'income', ?)
    """, (admin_id, amount, data["currency"], data["source"], message.text))

    commit()

    log_action(
        actor_id=manager_id,
        action="MANAGER_GIVE_ADMIN",
        details=f"{admin_name} ← {amount} {data['currency']}"
    )

    await notify_boss(
        f"💸 Menejer adminiga pul berdi\n\n"
        f"Menejer: {manager_name}\n"
        f"Admin: {admin_name}\n"
        f"Summa: {amount} {data['currency']}"
    )

    await message.answer("✅ Pul ajratildi")
    await state.clear()


# =========================
# 👥 ADMINLAR BALANSI
# =========================

@router.message(F.text == "👥 Adminlar balansi")
async def admins_balance(message: Message):
    manager = get_manager(message.from_user.id)
    if not manager:
        return

    manager_id = manager[0]

    cursor.execute("""
        SELECT full_name, balance
        FROM users
        WHERE parent_id=? AND role='admin'
    """, (manager_id,))

    rows = cursor.fetchall()
    if not rows:
        await message.answer("📭 Adminlar yo‘q")
        return

    text = "👥 Adminlar balansi\n\n"
    for name, balance in rows:
        text += f"{name}: {balance:,.0f}\n"

    await message.answer(text)


# =========================
# 📄 HISOBOT (PDF / EXCEL)
# =========================

@router.message(F.text == "📄 Hisobot")
async def report_start(message: Message, state: FSMContext):
    await state.set_state(BossPDF.date_from)
    await message.answer("📅 Boshlanish sana (YYYY-MM-DD):")


@router.message(BossPDF.date_from)
async def report_from(message: Message, state: FSMContext):
    await state.update_data(date_from=message.text)
    await state.set_state(BossPDF.date_to)
    await message.answer("📅 Tugash sana (YYYY-MM-DD):")


@router.message(BossPDF.date_to)
async def report_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    manager = get_manager(message.from_user.id)
    if not manager:
        await state.clear()
        return

    manager_id = manager[0]

    cursor.execute(
        "SELECT id FROM users WHERE parent_id=? OR id=?",
        (manager_id, manager_id)
    )
    user_ids = [r[0] for r in cursor.fetchall()]

    pdf = generate_pdf(user_ids, data["date_from"], message.text, f"manager_{manager_id}.pdf")
    excel = generate_excel(user_ids, data["date_from"], message.text, f"manager_{manager_id}.xlsx")

    await message.answer_document(FSInputFile(pdf))
    await message.answer_document(FSInputFile(excel))
    await state.clear()
