from database.db import cursor, commit


# =============================
#      BALANS OLISH
# =============================

def get_balance(user_id: int) -> float:
    cursor.execute(
        "SELECT balance FROM users WHERE id=?",
        (user_id,)
    )
    row = cursor.fetchone()
    return row[0] if row else 0.0


# =============================
#      BALANS O‘ZGARTIRISH
# =============================

def add_balance(user_id: int, amount: float):
    cursor.execute(
        "UPDATE users SET balance = balance + ? WHERE id=?",
        (amount, user_id)
    )
    commit()


def subtract_balance(user_id: int, amount: float):
    cursor.execute(
        "UPDATE users SET balance = balance - ? WHERE id=?",
        (amount, user_id)
    )
    commit()


# =============================
#  IKKI USER BALANSI (TRANSFER)
# =============================

def transfer_balance(from_user: int, to_user: int, amount: float):
    """
    from_user → pul kamayadi
    to_user   → pul ko‘payadi
    """
    cursor.execute(
        "UPDATE users SET balance = balance - ? WHERE id=?",
        (amount, from_user)
    )
    cursor.execute(
        "UPDATE users SET balance = balance + ? WHERE id=?",
        (amount, to_user)
    )
    commit()
