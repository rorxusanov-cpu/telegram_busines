from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.db import cursor, commit
from services.notify import notify_boss
from services.audit import log_action

router = Router()

# =============================
#      INLINE TASDIQLASH
# =============================

@router.callback_query(F.data.startswith("approve:"))
async def approve_change(call: CallbackQuery):
    req_id = int(call.data.split(":")[1])

    # faqat manager
    cursor.execute(
        "SELECT id, full_name FROM users "
        "WHERE telegram_id=? AND role='manager'",
        (call.from_user.id,)
    )
    manager = cursor.fetchone()
    if not manager:
        await call.answer("❌ Ruxsat yo‘q", show_alert=True)
        return

    manager_id, manager_name = manager

    # so‘rovni olish
    cursor.execute("""
        SELECT cr.transaction_id, cr.admin_id,
               cr.old_amount, cr.new_amount,
               cr.currency, cr.source,
               t.type
        FROM change_requests cr
        JOIN transactions t ON t.id = cr.transaction_id
        WHERE cr.id=? AND cr.status='pending'
    """, (req_id,))
    req = cursor.fetchone()

    if not req:
        await call.answer("❌ So‘rov topilmadi yoki allaqachon ko‘rilgan", show_alert=True)
        return

    trx_id, admin_id, old, new, currency, source, trx_type = req

    # transaction update
    cursor.execute("""
        UPDATE transactions
        SET amount=?, currency=?, source=?
        WHERE id=?
    """, (new, currency, source, trx_id))

    # balans farqi
    diff = new - old

    if trx_type == "expense":
        cursor.execute("UPDATE users SET balance = balance - ? WHERE id=?", (diff, admin_id))
        cursor.execute("UPDATE users SET balance = balance - ? WHERE id=?", (diff, manager_id))
    else:  # income
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id=?", (diff, admin_id))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id=?", (diff, manager_id))

    # so‘rov status
    cursor.execute("""
        UPDATE change_requests
        SET status='approved', manager_id=?
        WHERE id=? AND status='pending'
    """, (manager_id, req_id))

    commit()

    # audit
    log_action(
        actor_id=manager_id,
        action="CHANGE_APPROVED",
        details=f"{old} → {new} {currency} ({trx_type})"
    )

    # admin nomi
    cursor.execute("SELECT full_name FROM users WHERE id=?", (admin_id,))
    admin_name = cursor.fetchone()[0]

    # bossga xabar
    await notify_boss(
        f"✏️ O‘ZGARTIRISH TASDIQLANDI\n\n"
        f"Admin: {admin_name}\n"
        f"{old} → {new} {currency}\n"
        f"Ruxsat bergan menejer: {manager_name}"
    )

    await call.message.edit_text("✅ So‘rov tasdiqlandi")
    await call.answer()


@router.callback_query(F.data.startswith("reject:"))
async def reject_change(call: CallbackQuery):
    req_id = int(call.data.split(":")[1])

    # faqat manager
    cursor.execute(
        "SELECT id FROM users WHERE telegram_id=? AND role='manager'",
        (call.from_user.id,)
    )
    if not cursor.fetchone():
        await call.answer("❌ Ruxsat yo‘q", show_alert=True)
        return

    cursor.execute("""
        UPDATE change_requests
        SET status='rejected'
        WHERE id=? AND status='pending'
    """, (req_id,))
    commit()

    await call.message.edit_text("❌ So‘rov rad etildi")
    await call.answer()
