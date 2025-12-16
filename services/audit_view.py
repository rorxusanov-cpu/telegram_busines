from database.db import cursor
from datetime import datetime


def get_audit(user_ids: list[int], date_from: str, date_to: str):
    # ❗ Agar user_ids bo‘sh bo‘lsa
    if not user_ids:
        return []

    placeholders = ",".join("?" for _ in user_ids)

    cursor.execute(f"""
        SELECT
            a.created_at,
            u.full_name,
            a.action,
            a.details
        FROM audit a
        JOIN users u ON u.id = a.actor_id
        WHERE a.actor_id IN ({placeholders})
          AND date(a.created_at) BETWEEN ? AND ?
        ORDER BY a.created_at DESC
    """, (*user_ids, date_from, date_to))

    return cursor.fetchall()


def format_audit(rows, date_from: str, date_to: str) -> str:
    if not rows:
        return "🔍 Audit bo‘yicha ma’lumot yo‘q"

    text = f"🔍 AUDIT\n📅 {date_from} → {date_to}\n\n"

    for created, name, action, details in rows:
        # Sana formatini chiroyli qilish
        try:
            created_fmt = datetime.fromisoformat(created).strftime("%d.%m.%Y %H:%M")
        except Exception:
            created_fmt = created

        text += (
            f"🕒 {created_fmt}\n"
            f"👤 {name}\n"
            f"⚙️ {action}\n"
            f"📝 {details}\n"
            f"----------------------\n"
        )

    return text
