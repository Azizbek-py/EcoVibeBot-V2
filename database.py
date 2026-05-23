import aiosqlite
import json
import os

DB_PATH = "challenge_bot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE NOT NULL,
                full_name TEXT,
                phone TEXT,
                address TEXT,
                score REAL DEFAULT 0,
                group_id INTEGER,
                registered_at TIMESTAMP DEFAULT (datetime('now', '+5 hours'))
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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS missions (
                id INTEGER PRIMARY KEY,
                mission_number INTEGER UNIQUE NOT NULL,
                title TEXT,
                description TEXT,
                file_id TEXT,
                file_type TEXT,
                created_at TIMESTAMP DEFAULT (datetime('now', '+5 hours')),
                is_active INTEGER DEFAULT 1
            )
        """)
        await db.execute("""
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
                submitted_at TIMESTAMP DEFAULT (datetime('now', '+5 hours')),
                scored_at TIMESTAMP,
                UNIQUE(user_telegram_id, mission_number)
            )
        """)
        # Deadline ustuni (mavjud bo'lmasa qo'shiladi)
        try:
            await db.execute("ALTER TABLE missions ADD COLUMN deadline TIMESTAMP DEFAULT NULL")
        except Exception:
            pass  # allaqachon bor

        # Missiya izohlari
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mission_comments (
                id INTEGER PRIMARY KEY,
                user_telegram_id INTEGER NOT NULL,
                mission_number INTEGER NOT NULL,
                comment TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT (datetime('now', '+5 hours'))
            )
        """)

        # Do'kon xaridlari
        await db.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY,
                user_telegram_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                item_name TEXT NOT NULL,
                price INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                approved_by INTEGER,
                created_at TIMESTAMP DEFAULT (datetime('now', '+5 hours')),
                approved_at TIMESTAMP
            )
        """)

        # VIP foydalanuvchilar
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
        # Count registered users to determine group
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            count = (await cur.fetchone())[0]
        group_number = (count // 25) + 1

        # Ensure group exists
        await db.execute("INSERT OR IGNORE INTO groups (group_number) VALUES (?)", (group_number,))

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
        async with db.execute("SELECT * FROM users WHERE group_id=? ORDER BY score DESC", (group_number,)) as cur:
            return await cur.fetchall()

async def update_user_score(telegram_id: int, delta: float) -> tuple:
    """Ballni yangilaydi. Daraja o'zgarsa (old_level, new_level), aks holda (None, None)."""
    from levels import get_level
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT score FROM users WHERE telegram_id=?", (telegram_id,)) as cur:
            row = await cur.fetchone()
        old_score = row["score"] if row else 0
        old_level = get_level(old_score)
        new_score = old_score + delta
        new_level = get_level(new_score)
        await db.execute("UPDATE users SET score = ? WHERE telegram_id=?", (new_score, telegram_id))
        await db.commit()
    if old_level != new_level:
        return old_level, new_level
    return None, None

async def set_user_score(telegram_id: int, score: float) -> tuple:
    from levels import get_level
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT score FROM users WHERE telegram_id=?", (telegram_id,)) as cur:
            row = await cur.fetchone()
        old_score = row["score"] if row else 0
        old_level = get_level(old_score)
        new_level = get_level(score)
        await db.execute("UPDATE users SET score = ? WHERE telegram_id=?", (score, telegram_id))
        await db.commit()
    if old_level != new_level:
        return old_level, new_level
    return None, None

async def update_user_profile(telegram_id: int, full_name: str = None, address: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        if full_name:
            await db.execute("UPDATE users SET full_name=? WHERE telegram_id=?", (full_name, telegram_id))
        if address:
            await db.execute("UPDATE users SET address=? WHERE telegram_id=?", (address, telegram_id))
        await db.commit()

async def find_user(query: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        try:
            tid = int(query)
            async with db.execute("SELECT * FROM users WHERE telegram_id=?", (tid,)) as cur:
                return await cur.fetchone()
        except ValueError:
            async with db.execute("SELECT * FROM users WHERE full_name LIKE ?", (f"%{query}%",)) as cur:
                return await cur.fetchone()

async def get_top_users(limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY score DESC LIMIT ?", (limit,)) as cur:
            return await cur.fetchall()

# ---- Coordinators ----
async def add_coordinator(telegram_id: int, full_name: str, username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO coordinators (telegram_id, full_name, username) VALUES (?,?,?)",
            (telegram_id, full_name, username)
        )
        await db.commit()

async def remove_coordinator(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM coordinators WHERE telegram_id=?", (telegram_id,))
        await db.execute("DELETE FROM group_coordinators WHERE coordinator_id=?", (telegram_id,))
        await db.commit()

async def get_coordinators():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM coordinators") as cur:
            return await cur.fetchall()

async def get_coordinator(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM coordinators WHERE telegram_id=?", (telegram_id,)) as cur:
            return await cur.fetchone()

async def get_coordinator_groups(coordinator_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT group_number FROM group_coordinators WHERE coordinator_id=?", (coordinator_id,)) as cur:
            rows = await cur.fetchall()
            return [r["group_number"] for r in rows]

async def assign_coordinator_to_group(group_number: int, coordinator_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        # Check how many coordinators assigned to this group
        async with db.execute("SELECT COUNT(*) FROM group_coordinators WHERE group_number=?", (group_number,)) as cur:
            count = (await cur.fetchone())[0]
        if count >= 2:
            return False, "Guruhga allaqachon 2 ta coordinator tayinlangan!"
        # Check coordinator in list
        async with db.execute("SELECT * FROM coordinators WHERE telegram_id=?", (coordinator_id,)) as cur:
            coord = await cur.fetchone()
        if not coord:
            return False, "Bu ID koordinatorlar ro'yxatida yo'q!"
        await db.execute(
            "INSERT OR IGNORE INTO group_coordinators (group_number, coordinator_id) VALUES (?,?)",
            (group_number, coordinator_id)
        )
        await db.commit()
        return True, "Muvaffaqiyatli tayinlandi!"

async def get_group_coordinators(group_number: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT c.* FROM coordinators c
            JOIN group_coordinators gc ON c.telegram_id = gc.coordinator_id
            WHERE gc.group_number=?
        """, (group_number,)) as cur:
            return await cur.fetchall()

# ---- Inspectors ----
async def add_inspector(telegram_id: int, full_name: str, username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO inspectors (telegram_id, full_name, username) VALUES (?,?,?)",
            (telegram_id, full_name, username)
        )
        await db.commit()

async def remove_inspector(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM inspectors WHERE telegram_id=?", (telegram_id,))
        await db.commit()

async def get_inspectors():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM inspectors") as cur:
            return await cur.fetchall()

async def get_inspector(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM inspectors WHERE telegram_id=?", (telegram_id,)) as cur:
            return await cur.fetchone()

# ---- Missions ----
async def add_mission(mission_number: int, title: str, description: str, file_id: str = None, file_type: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO missions (mission_number, title, description, file_id, file_type) VALUES (?,?,?,?,?)",
            (mission_number, title, description, file_id, file_type)
        )
        await db.commit()

async def delete_mission(mission_number: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM missions WHERE mission_number=?", (mission_number,))
        await db.commit()

async def get_missions(active_only=True):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if active_only:
            async with db.execute("SELECT * FROM missions WHERE is_active=1 ORDER BY mission_number") as cur:
                return await cur.fetchall()
        else:
            async with db.execute("SELECT * FROM missions ORDER BY mission_number") as cur:
                return await cur.fetchall()

async def get_mission(mission_number: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM missions WHERE mission_number=?", (mission_number,)) as cur:
            return await cur.fetchone()

# ---- Submissions ----
async def submit_mission(user_telegram_id: int, mission_number: int, content: str, file_id: str = None, file_type: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO mission_submissions 
            (user_telegram_id, mission_number, content, file_id, file_type)
            VALUES (?,?,?,?,?)
        """, (user_telegram_id, mission_number, content, file_id, file_type))
        await db.commit()

async def get_submission(user_telegram_id: int, mission_number: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM mission_submissions WHERE user_telegram_id=? AND mission_number=?",
            (user_telegram_id, mission_number)
        ) as cur:
            return await cur.fetchone()

async def score_submission(submission_id: int, quality_score: float, time_score: float, scored_by: int):
    """Topshiriqni baholaydi. (user_id, old_level, new_level) qaytaradi yoki (user_id, None, None)."""
    from levels import get_level
    final = (quality_score + time_score) / 2
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT user_telegram_id, final_score FROM mission_submissions WHERE id=?", (submission_id,)) as cur:
            row = await cur.fetchone()
        if not row:
            return None, None, None
        old_final = row["final_score"] or 0
        user_id = row["user_telegram_id"]
        # Oldingi ball
        async with db.execute("SELECT score FROM users WHERE telegram_id=?", (user_id,)) as cur:
            urow = await cur.fetchone()
        old_score = urow["score"] if urow else 0
        old_level = get_level(old_score)
        new_score = old_score - old_final + final
        new_level = get_level(new_score)
        await db.execute("""
            UPDATE mission_submissions 
            SET quality_score=?, time_score=?, final_score=?, scored_by=?, scored_at=datetime('now', '+5 hours')
            WHERE id=?
        """, (quality_score, time_score, final, scored_by, submission_id))
        await db.execute("UPDATE users SET score = ? WHERE telegram_id=?", (new_score, user_id))
        await db.commit()
    if old_level != new_level:
        return user_id, old_level, new_level
    return user_id, None, None

async def get_submissions_for_mission(mission_number: int, group_number: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if group_number is not None:
            async with db.execute("""
                SELECT ms.*, u.full_name, u.group_id FROM mission_submissions ms
                JOIN users u ON ms.user_telegram_id = u.telegram_id
                WHERE ms.mission_number=? AND u.group_id=?
                ORDER BY ms.submitted_at
            """, (mission_number, group_number)) as cur:
                return await cur.fetchall()
        else:
            async with db.execute("""
                SELECT ms.*, u.full_name, u.group_id FROM mission_submissions ms
                JOIN users u ON ms.user_telegram_id = u.telegram_id
                WHERE ms.mission_number=?
                ORDER BY ms.submitted_at
            """, (mission_number,)) as cur:
                return await cur.fetchall()

async def get_all_submissions():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT ms.*, u.full_name, u.group_id FROM mission_submissions ms
            JOIN users u ON ms.user_telegram_id = u.telegram_id
            WHERE ms.final_score IS NULL
            ORDER BY ms.submitted_at
        """) as cur:
            return await cur.fetchall()

async def get_unscored_submissions_for_coordinator(coordinator_id: int):
    """Get unscored submissions from users in coordinator's groups"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        groups = await get_coordinator_groups(coordinator_id)
        if not groups:
            return []
        placeholders = ",".join("?" * len(groups))
        async with db.execute(f"""
            SELECT ms.*, u.full_name, u.group_id FROM mission_submissions ms
            JOIN users u ON ms.user_telegram_id = u.telegram_id
            WHERE ms.final_score IS NULL AND u.group_id IN ({placeholders})
            ORDER BY ms.submitted_at
        """, groups) as cur:
            return await cur.fetchall()

async def get_scored_submissions(mission_number: int = None, group_number: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = """
            SELECT ms.*, u.full_name, u.group_id FROM mission_submissions ms
            JOIN users u ON ms.user_telegram_id = u.telegram_id
            WHERE ms.final_score IS NOT NULL
        """
        params = []
        if mission_number:
            query += " AND ms.mission_number=?"
            params.append(mission_number)
        if group_number:
            query += " AND u.group_id=?"
            params.append(group_number)
        query += " ORDER BY ms.submitted_at"
        async with db.execute(query, params) as cur:
            return await cur.fetchall()

# ── Statistika ─────────────────────────────────────────────────
async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT COUNT(*) as cnt FROM users") as cur:
            total_users = (await cur.fetchone())["cnt"]
        async with db.execute("SELECT COUNT(*) as cnt FROM missions WHERE is_active=1") as cur:
            total_missions = (await cur.fetchone())["cnt"]
        async with db.execute("SELECT COUNT(*) as cnt FROM mission_submissions") as cur:
            total_subs = (await cur.fetchone())["cnt"]
        async with db.execute("SELECT COUNT(*) as cnt FROM mission_submissions WHERE final_score IS NOT NULL") as cur:
            scored_subs = (await cur.fetchone())["cnt"]
        async with db.execute("SELECT AVG(score) as avg FROM users") as cur:
            avg_score = (await cur.fetchone())["avg"] or 0
        async with db.execute("SELECT COUNT(*) as cnt FROM coordinators") as cur:
            total_coords = (await cur.fetchone())["cnt"]
        async with db.execute("SELECT COUNT(*) as cnt FROM inspectors") as cur:
            total_insp = (await cur.fetchone())["cnt"]
        async with db.execute("SELECT COUNT(DISTINCT group_id) as cnt FROM users") as cur:
            total_groups = (await cur.fetchone())["cnt"]
        return {
            "total_users": total_users,
            "total_missions": total_missions,
            "total_submissions": total_subs,
            "scored_submissions": scored_subs,
            "avg_score": round(avg_score, 2),
            "total_coordinators": total_coords,
            "total_inspectors": total_insp,
            "total_groups": total_groups,
        }

# ── Kunlik/haftalik reyting ────────────────────────────────────
async def get_periodic_rating(period: str = "daily", limit: int = 10):
    """period: 'daily' | 'weekly'"""
    if period == "daily":
        interval = "'-1 day'"
    else:
        interval = "'-7 days'"
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = f"""
            SELECT u.full_name, u.telegram_id, u.group_id,
                   SUM(ms.final_score) as period_score,
                   COUNT(ms.id) as mission_count
            FROM mission_submissions ms
            JOIN users u ON ms.user_telegram_id = u.telegram_id
            WHERE ms.scored_at >= datetime('now', '+5 hours', {interval})
              AND ms.final_score IS NOT NULL
            GROUP BY ms.user_telegram_id
            ORDER BY period_score DESC
            LIMIT ?
        """
        async with db.execute(query, (limit,)) as cur:
            return await cur.fetchall()

# ── Deadline ───────────────────────────────────────────────────
async def set_mission_deadline(mission_number: int, deadline: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE missions SET deadline=? WHERE mission_number=?",
            (deadline, mission_number)
        )
        await db.commit()

async def is_mission_open(mission_number: int) -> tuple:
    """(is_open: bool, deadline_str: str | None)"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT deadline FROM missions WHERE mission_number=?", (mission_number,)) as cur:
            row = await cur.fetchone()
        if not row or not row["deadline"]:
            return True, None
        async with db.execute("SELECT datetime('now', '+5 hours') <= ? as open_val", (row["deadline"],)) as cur:
            res = await cur.fetchone()
        return bool(res[0]), row["deadline"]

# ── Izohlar ────────────────────────────────────────────────────
async def add_comment(user_telegram_id: int, mission_number: int, comment: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO mission_comments (user_telegram_id, mission_number, comment) VALUES (?,?,?)",
            (user_telegram_id, mission_number, comment)
        )
        await db.commit()

async def get_comments(mission_number: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT mc.*, u.full_name FROM mission_comments mc
            JOIN users u ON mc.user_telegram_id = u.telegram_id
            WHERE mc.mission_number=?
            ORDER BY mc.created_at DESC
            LIMIT 20
        """, (mission_number,)) as cur:
            return await cur.fetchall()

# ── Do'kon ─────────────────────────────────────────────────────
async def buy_item(user_telegram_id: int, item_id: str, item_name: str, price: int) -> tuple:
    """
    Xarid qilish. Ballar yetarli bo'lsa (old_level, new_level) qaytaradi.
    Yetarli bo'lmasa (None, 'not_enough') qaytaradi.
    """
    from levels import get_level
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT score FROM users WHERE telegram_id=?", (user_telegram_id,)) as cur:
            row = await cur.fetchone()
        if not row or row["score"] < price:
            return None, "not_enough"
        old_score = row["score"]
        old_level = get_level(old_score)
        new_score = old_score - price
        new_level = get_level(new_score)

        # VIP bo'lsa belgi qo'yish
        if item_id == "vip":
            await db.execute("UPDATE users SET is_vip=1 WHERE telegram_id=?", (user_telegram_id,))

        await db.execute("UPDATE users SET score=? WHERE telegram_id=?", (new_score, user_telegram_id))
        await db.execute(
            "INSERT INTO purchases (user_telegram_id, item_id, item_name, price, status) VALUES (?,?,?,?,'completed')",
            (user_telegram_id, item_id, item_name, price)
        )
        await db.commit()

    if old_level != new_level:
        return old_level, new_level
    return None, None

async def get_user_purchases(user_telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM purchases WHERE user_telegram_id=? ORDER BY created_at DESC",
            (user_telegram_id,)
        ) as cur:
            return await cur.fetchall()

async def get_all_purchases(limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT p.*, u.full_name, u.group_id FROM purchases p
            JOIN users u ON p.user_telegram_id = u.telegram_id
            ORDER BY p.created_at DESC LIMIT ?
        """, (limit,)) as cur:
            return await cur.fetchall()

async def revoke_vip(user_telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_vip=0 WHERE telegram_id=?", (user_telegram_id,))
        await db.commit()
