from aiogram import Bot
from config import BOSS_IDS


async def notify_boss(bot: Bot, text: str):
    """
    Bosslarga xabar yuborish
    Bot instance tashqaridan beriladi (app.py dan)
    """
    for boss_id in BOSS_IDS:
        try:
            await bot.send_message(boss_id, text)
        except Exception:
            # agar bitta bossga yuborilmasa ham boshqalariga ketadi
            pass
