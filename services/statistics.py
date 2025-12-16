from database.db import cursor


def get_statistics(user_ids: list[int], date_from: str, date_to: str):
    """
    user_ids: qaysi userlar bo‘yicha
    date_from, date_to: YYYY-MM-DD
    """

    # ❗ Agar user_ids bo‘sh bo‘lsa
    if not user_ids:
        return {}

    placeholders = ",".join("?" for _ in user_ids)

    cursor.execute(f"""
        SELECT
            type,
            currency,
            source,
            SUM(amount)
        FROM transactions
        WHERE user_id IN ({placeholders})
          AND date(created_at) BETWEEN ? AND ?
        GROUP BY type, currency, source
    """, (*user_ids, date_from, date_to))

    rows = cursor.fetchall()

    stats = {}

    for typ, currency, source, total in rows:
        stats.setdefault(currency, {})
        stats[currency].setdefault(typ, {})
        stats[currency][typ][source] = total

    return stats


def format_statistics(stats: dict, date_from: str, date_to: str) -> str:
    if not stats:
        return "📊 Bu davr uchun ma’lumot yo‘q"

    text = (
        f"📊 STATISTIKA\n"
        f"📅 {date_from} → {date_to}\n\n"
    )

    for currency, data in stats.items():
        text += f"💱 {currency}\n"

        # Avval Kirim, keyin Chiqim
        for typ in ("income", "expense"):
            if typ not in data:
                continue

            text += "➕ Kirim\n" if typ == "income" else "➖ Chiqim\n"

            for source, amount in data[typ].items():
                src = "Karta" if source in ("karta", "card") else "Naqd"
                text += f"   {src}: {amount:,.0f}\n"

        text += "\n"

    return text
