from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from aiogram import Bot
from aiogram.types import FSInputFile

from database.db import cursor
from config import BOSS_IDS
from services.statistics import get_statistics, format_statistics
from services.pdf import generate_pdf
from services.excel import generate_excel


def setup_scheduler(bot: Bot):
    """
    Scheduler faqat app.py dan chaqiriladi
    """
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

    # =============================
    # 📆 KUNLIK STATISTIKA (23:59)
    # =============================
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

    # =============================
    # 📆 HAFTALIK PDF (DUSHANBA)
    # =============================
    async def weekly_pdf():
        today = datetime.now()
        start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")

        # 👑 Boss
        cursor.execute("SELECT id FROM users")
        user_ids = [r[0] for r in cursor.fetchall()]

        pdf_path = generate_pdf(user_ids, start, end, "weekly_boss.pdf")

        for boss_id in BOSS_IDS:
            await bot.send_document(boss_id, FSInputFile(pdf_path))

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

            pdf = generate_pdf(ids, start, end, f"weekly_manager_{manager_id}.pdf")
            await bot.send_document(tg_id, FSInputFile(pdf))

    # =============================
    # 📆 OYLIK PDF + EXCEL (OY OXIRI)
    # =============================
    async def monthly_report():
        today = datetime.now()
        start = today.replace(day=1).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")

        cursor.execute("SELECT id FROM users")
        user_ids = [r[0] for r in cursor.fetchall()]

        pdf = generate_pdf(user_ids, start, end, "month_boss.pdf")
        excel = generate_excel(user_ids, start, end, "month_boss.xlsx")

        for boss_id in BOSS_IDS:
            await bot.send_document(boss_id, FSInputFile(pdf))
            await bot.send_document(boss_id, FSInputFile(excel))

    # ===== JOBLAR =====
    scheduler.add_job(daily_report, "cron", hour=23, minute=59)
    scheduler.add_job(weekly_pdf, "cron", day_of_week="mon", hour=9, minute=0)
    scheduler.add_job(monthly_report, "cron", day=28, hour=9, minute=0)

    scheduler.start()
