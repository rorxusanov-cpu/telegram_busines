from database.db import cursor, commit
def create_change_requests():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS change_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER,
        admin_id INTEGER,
        old_amount REAL,
        new_amount REAL,
        currency TEXT,
        source TEXT,
        comment TEXT,
        status TEXT DEFAULT 'pending',
        manager_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    commit()
