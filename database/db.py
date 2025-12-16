import sqlite3

DB_NAME = "database/bot.db"

# 🔌 Ulanish
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
conn.row_factory = sqlite3.Row

# 📌 Cursor
cursor = conn.cursor()


def commit():
    conn.commit()
