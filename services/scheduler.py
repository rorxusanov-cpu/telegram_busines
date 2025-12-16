from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from aiogram import Bot

from config import BOT_TOKEN, BOSS_IDS
from database.db import cursor
from services.statistics import get_statistics, format_statistics
from services.pdf import generate_pdf
from services.excel import generate_excel

# 🇺🇿 O‘zbekiston vaqti
scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

bot = Bot(BOT_TOKEN)


# ==============================
# 📊 KUNLIK HISOBOT (23:59)
# ==============================
async def daily_report():
    today = datetime.now().strftime("%Y-%m-%d")

    # 👑 Boss
    cursor.execute("SELECT id FROM users")
    all_user_ids = [r[0] for r in cursor.fetchall()]

    stats = get_statistics(all_user_ids, today, today)
    text = format_statistics(stats, today, today)

    for boss_id in BOSS_IDS:
        await bot.send_message(boss_id, text)

    # 👤 Menejerlar
    cursor.execute("SELECT id, telegram_id FROM users WHERE role='manager'")
    managers = cursor.fetchall()

    for manager_id, tg_id in managers:
        cursor.execute(
            "SELECT id FROM users WHERE parent_id=? AND role='admin'",
            (manager_id,)
        )
        admin_ids = [r[0] for r in cursor.fetchall()]
        user_ids = admin_ids + [manager_id]

        stats = get_statistics(user_ids, today, today)
        text = format_statistics(stats, today, today)

        await bot.send_message(tg_id, text)


# ==============================
# 📄 HAFTALIK PDF (DUSHANBA)
# ==============================
async def weekly_pdf():
    today = datetime.now()
    start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")

    # 👑 Boss
    cursor.execute("SELECT id FROM users")
    user_ids = [r[0] for r in cursor.fetchall()]

    pdf_path = generate_pdf(user_ids, start, end, "weekly_boss.pdf")

    for boss_id in BOSS_IDS:
        await bot.send_document(boss_id, pdf_path)

    # 👤 Menejerlar
    cursor.execute("SELECT id, telegram_id FROM users WHERE role='manager'")
    managers = cursor.fetchall()

    for manager_id, tg_id in managers:
        cursor.execute(
            "SELECT id FROM users WHERE parent_id=? AND role='admin'",
            (manager_id,)
        )
        admin_ids = [r[0] for r in cursor.fetchall()]
        ids = admin_ids + [manager_id]

        pdf_path = generate_pdf(
            ids,
            start,
            end,
            f"weekly_manager_{manager_id}.pdf"
        )
        await bot.send_document(tg_id, pdf_path)


# ==============================
# 📊 OYLIK PDF + EXCEL (28-kuni)
# ==============================
async def monthly_report():
    today = datetime.now()
    start = today.replace(day=1).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")

    cursor.execute("SELECT id FROM users")
    user_ids = [r[0] for r in cursor.fetchall()]

    pdf_path = generate_pdf(user_ids, start, end, "month_boss.pdf")
    excel_path = generate_excel(user_ids, start, end, "month_boss.xlsx")

    for boss_id in BOSS_IDS:
        await bot.send_document(boss_id, pdf_path)
        await bot.send_document(boss_id, excel_path)
