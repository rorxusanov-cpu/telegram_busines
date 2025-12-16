import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database.db import init_db

# --------------------
# Routers
# --------------------
from handlers.start import router as start_router
from handlers.cancel import router as cancel_router
from handlers.expenses import router as expenses_router
from handlers.manager import router as manager_router
from handlers.boss import router as boss_router
from handlers.approvals import router as approvals_router

# --------------------
# Scheduler
# --------------------
from services.scheduler import (
    scheduler,
    daily_report,
    weekly_pdf,
    monthly_report,
)

# ====================
# MAIN
# ====================

async def main():
    # --- DB init ---
    init_db()

    # --- Bot & Dispatcher ---
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # --- Routers ---
    dp.include_router(start_router)
    dp.include_router(cancel_router)
    dp.include_router(expenses_router)
    dp.include_router(manager_router)
    dp.include_router(boss_router)
    dp.include_router(approvals_router)

    # --------------------
    # Scheduler jobs
    # --------------------

    # 🇺🇿 HAR KUNI 23:59
    scheduler.add_job(
        daily_report,
        "cron",
        hour=23,
        minute=59
    )

    # 📆 HAR DUSHANBA 09:00
    scheduler.add_job(
        weekly_pdf,
        "cron",
        day_of_week="mon",
        hour=9,
        minute=0
    )

    # 📆 OYLIK (28-kuni, xavfsiz)
    scheduler.add_job(
        monthly_report,
        "cron",
        day=28,
        hour=10,
        minute=0
    )

    scheduler.start()

    # --- Start polling ---
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
