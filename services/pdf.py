from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from datetime import datetime
import os

from database.db import cursor


def generate_pdf(
    user_ids: list[int],
    date_from: str,
    date_to: str,
    file_name: str
) -> str:
    """
    user_ids: kimlar bo‘yicha (admin / menejer / boss)
    date_from, date_to: YYYY-MM-DD
    """

    # ❗ Agar user_ids bo‘sh bo‘lsa
    if not user_ids:
        raise ValueError("user_ids bo‘sh bo‘lishi mumkin emas")

    file_path = os.path.join("/mnt/data", file_name)

    placeholders = ",".join("?" for _ in user_ids)

    cursor.execute(f"""
        SELECT
            t.created_at,
            u.full_name,
            t.type,
            t.amount,
            t.currency,
            t.source,
            t.comment
        FROM transactions t
        JOIN users u ON u.id = t.user_id
        WHERE t.user_id IN ({placeholders})
          AND date(t.created_at) BETWEEN ? AND ?
        ORDER BY t.created_at
    """, (*user_ids, date_from, date_to))

    rows = cursor.fetchall()

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=20,
        leftMargin=20,
        topMargin=30,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()
    elements = []

    # ===== TITLE =====
    title = Paragraph(
        f"<b>Moliyaviy hisobot</b><br/>"
        f"<font size=10>{date_from} → {date_to}</font>",
        styles["Title"]
    )
    elements.append(title)

    # ===== TABLE HEADER =====
    data = [[
        "Sana",
        "Kim",
        "Amal",
        "Summa",
        "Valyuta",
        "Manba",
        "Izoh"
    ]]

    total = {}

    for created, name, typ, amount, currency, source, comment in rows:
        # Sana formatlash
        try:
            created_fmt = datetime.fromisoformat(created).strftime("%d.%m.%Y %H:%M")
        except Exception:
            created_fmt = created

        data.append([
            created_fmt,
            name,
            "Kirim" if typ == "income" else "Chiqim",
            f"{amount:,.0f}",
            currency,
            "Karta" if source in ("karta", "card") else "Naqd",
            comment or ""
        ])

        key = (currency, typ)
        total[key] = total.get(key, 0) + amount

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("ALIGN", (3, 1), (3, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))

    elements.append(table)

    # ===== TOTALS =====
    elements.append(Paragraph("<br/><b>Jami:</b>", styles["Heading2"]))

    for (currency, typ), amount in total.items():
        elements.append(
            Paragraph(
                f"{'Kirim' if typ=='income' else 'Chiqim'} "
                f"{currency}: {amount:,.0f}",
                styles["Normal"]
            )
        )

    doc.build(elements)

    return file_path
