import aiosqlite

DB_PATH = 'users.db'

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица пользователей (анкеты)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                genre TEXT
            )
        """)
        # Таблица данных артистов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS artist_data (
                user_id      INTEGER PRIMARY KEY,
                balance      REAL    DEFAULT 0,
                tariff       TEXT    DEFAULT 'MINI',
                tracks_count INTEGER DEFAULT 0
            )
        """)
        await db.commit()

async def save_user(user_id: int, name: str, email: str, genre: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO users(user_id, name, email, genre)
            VALUES (?, ?, ?, ?)
        """, (user_id, name, email, genre))
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT name, email, genre FROM users WHERE user_id = ?", (user_id,))
        return await cursor.fetchone()

async def get_artist(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT balance, tariff, tracks_count
            FROM artist_data
            WHERE user_id = ?
        """, (user_id,))
        return await cursor.fetchone()

async def upsert_artist(user_id: int,
                        balance: float = None,
                        tariff: str = None,
                        tracks_count: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT balance, tariff, tracks_count
            FROM artist_data
            WHERE user_id = ?
        """, (user_id,))
        existing = await cursor.fetchone()
        if existing:
            cur_bal, cur_tariff, cur_tracks = existing
        else:
            cur_bal, cur_tariff, cur_tracks = 0.0, 'MINI', 0

        new_bal    = balance      if balance      is not None else cur_bal
        new_tariff = tariff       if tariff       is not None else cur_tariff
        new_tracks = tracks_count if tracks_count is not None else cur_tracks

        await db.execute("""
            INSERT OR REPLACE INTO artist_data(user_id, balance, tariff, tracks_count)
            VALUES (?, ?, ?, ?)
        """, (user_id, new_bal, new_tariff, new_tracks))
        await db.commit()
