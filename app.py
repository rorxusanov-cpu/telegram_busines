import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from services.scheduler import setup_scheduler

# ===== HANDLERS =====
from handlers.start import router as start_router
from handlers.admin import router as admin_router
from handlers.manager import router as manager_router
from handlers.boss import router as boss_router
from handlers.approvals import router as approvals_router
from handlers.expenses import router as expenses_router
from handlers.cancel import router as cancel_router


async def main():
    # 🤖 Bot
    bot = Bot(token=BOT_TOKEN)

    # 📦 Dispatcher + FSM
    dp = Dispatcher(storage=MemoryStorage())

    # 🔗 Routerlar
    dp.include_router(start_router)
    dp.include_router(cancel_router)

    dp.include_router(admin_router)
    dp.include_router(manager_router)
    dp.include_router(boss_router)

    dp.include_router(approvals_router)
    dp.include_router(expenses_router)

    # ⏰ Scheduler (23:59, haftalik, oylik)
    setup_scheduler(bot)

    # 🚀 Botni ishga tushirish
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
