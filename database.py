import aiosqlite
import datetime

async def init_db():
    async with aiosqlite.connect('payments.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT
            )
        ''')
        await db.commit()

async def add_pending_payment(user_id: int, username: str):
    created = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    async with aiosqlite.connect('payments.db') as db:
        await db.execute(
            "INSERT OR REPLACE INTO payments (user_id, username, status, created_at) VALUES (?, ?, 'pending', ?)",
            (user_id, username, created)
        )
        await db.commit()

async def approve_payment(user_id: int):
    async with aiosqlite.connect('payments.db') as db:
        await db.execute("UPDATE payments SET status = 'approved' WHERE user_id = ?", (user_id,))
        await db.commit()
