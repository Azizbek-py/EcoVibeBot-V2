import aiosqlite
import json
import os

DB_PATH = "challenge_bot.db"
SQLITE_NOW = "datetime('now', '+5 hours')"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE NOT NULL,
                full_name TEXT,
                phone TEXT,
                address TEXT,
                score REAL DEFAULT 0,
                group_id INTEGER,
                registered_at TIMESTAMP DEFAULT ({SQLITE_NOW}),
                is_vip INTEGER DEFAULT 0
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS coordinators (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE NOT NULL,
                full_name TEXT,
                username TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS inspectors (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE NOT NULL,
                full_name TEXT,
                username TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY,
                group_number INTEGER UNIQUE NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS group_coordinators (
                id INTEGER PRIMARY KEY,
                group_number INTEGER NOT NULL,
                coordinator_id INTEGER NOT NULL,
                UNIQUE(group_number, coordinator_id)
            )
        """)

        await db.execute(f"""
            CREATE TABLE IF NOT EXISTS missions (
                id INTEGER PRIMARY KEY,
                mission_number INTEGER UNIQUE NOT NULL,
                title TEXT,
                description TEXT,
                file_id TEXT,
                file_type TEXT,
                deadline TIMESTAMP DEFAULT NULL,
                created_at TIMESTAMP DEFAULT ({SQLITE_NOW}),
                is_active INTEGER DEFAULT 1
            )
        """)

        await db.execute(f"""
            CREATE TABLE IF NOT EXISTS mission_submissions (
                id INTEGER PRIMARY KEY,
                user_telegram_id INTEGER NOT NULL,
                mission_number INTEGER NOT NULL,
                content TEXT,
                file_id TEXT,
                file_type TEXT,
                quality_score REAL DEFAULT NULL,
                time_score REAL DEFAULT NULL,
                final_score REAL DEFAULT NULL,
                scored_by INTEGER,
                submitted_at TIMESTAMP DEFAULT ({SQLITE_NOW}),
                scored_at TIMESTAMP,
                UNIQUE(user_telegram_id, mission_number)
            )
        """)

        try:
            await db.execute("ALTER TABLE missions ADD COLUMN deadline TIMESTAMP DEFAULT NULL")
        except Exception:
            pass

        await db.execute(f"""
            CREATE TABLE IF NOT EXISTS mission_comments (
                id INTEGER PRIMARY KEY,
                user_telegram_id INTEGER NOT NULL,
                mission_number INTEGER NOT NULL,
                comment TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT ({SQLITE_NOW})
            )
        """)

        await db.execute(f"""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY,
                user_telegram_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                item_name TEXT NOT NULL,
                price INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                approved_by INTEGER,
                created_at TIMESTAMP DEFAULT ({SQLITE_NOW}),
                approved_at TIMESTAMP
            )
        """)

        try:
            await db.execute("ALTER TABLE users ADD COLUMN is_vip INTEGER DEFAULT 0")
        except Exception:
            pass

        await db.commit()

async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)) as cur:
            return await cur.fetchone()

async def register_user(telegram_id: int, full_name: str, phone: str, address: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            count = (await cur.fetchone())[0]

        group_number = (count // 25) + 1

        await db.execute(
            "INSERT OR IGNORE INTO groups (group_number) VALUES (?)",
            (group_number,)
        )

        await db.execute(
            "INSERT OR REPLACE INTO users (telegram_id, full_name, phone, address, group_id) VALUES (?,?,?,?,?)",
            (telegram_id, full_name, phone, address, group_number)
        )

        await db.commit()

        return group_number

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY score DESC") as cur:
            return await cur.fetchall()

async def get_users_by_group(group_number: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE group_id=? ORDER BY score DESC",
            (group_number,)
        ) as cur:
            return await cur.fetchall()

async def update_user_score(telegram_id: int, delta: float) -> tuple:
    from levels import get_level

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            "SELECT score FROM users WHERE telegram_id=?",
            (telegram_id,)
        ) as cur:
            row = await cur.fetchone()

        old_score = row["score"] if row else 0
        old_level = get_level(old_score)

        new_score = old_score + delta
        new_level = get_level(new_score)

        await db.execute(
            "UPDATE users SET score=? WHERE telegram_id=?",
            (new_score, telegram_id)
        )

        await db.commit()

    if old_level != new_level:
        return old_level, new_level

    return None, None

async def set_user_score(telegram_id: int, score: float) -> tuple:
    from levels import get_level

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            "SELECT score FROM users WHERE telegram_id=?",
            (telegram_id,)
        ) as cur:
            row = await cur.fetchone()

        old_score = row["score"] if row else 0
        old_level = get_level(old_score)

        new_level = get_level(score)

        await db.execute(
            "UPDATE users SET score=? WHERE telegram_id=?",
            (score, telegram_id)
        )

        await db.commit()

    if old_level != new_level:
        return old_level, new_level

    return None, None

async def update_user_profile(
    telegram_id: int,
    full_name: str = None,
    address: str = None
):
    async with aiosqlite.connect(DB_PATH) as db:
        if full_name:
            await db.execute(
                "UPDATE users SET full_name=? WHERE telegram_id=?",
                (full_name, telegram_id)
            )

        if address:
            await db.execute(
                "UPDATE users SET address=? WHERE telegram_id=?",
                (address, telegram_id)
            )

        await db.commit()

async def find_user(query: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        try:
            tid = int(query)

            async with db.execute(
                "SELECT * FROM users WHERE telegram_id=?",
                (tid,)
            ) as cur:
                return await cur.fetchone()

        except ValueError:
            async with db.execute(
                "SELECT * FROM users WHERE full_name LIKE ?",
                (f"%{query}%",)
            ) as cur:
                return await cur.fetchone()

async def get_top_users(limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            "SELECT * FROM users ORDER BY score DESC LIMIT ?",
            (limit,)
        ) as cur:
            return await cur.fetchall()