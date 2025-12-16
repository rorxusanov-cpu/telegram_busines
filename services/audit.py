from database.db import cursor, commit
from datetime import datetime
import pytz

TZ = pytz.timezone("Asia/Tashkent")


def log_action(actor_id: int, action: str, details: str | None = None):
    created_at = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO audit (actor_id, action, details, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        actor_id,
        action,
        details if details else "—",
        created_at
    ))
    commit()
