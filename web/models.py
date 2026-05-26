import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "notes.db")


def _get_connection():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            title TEXT,
            content TEXT,
            author TEXT,
            created_at TEXT,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            heat INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id TEXT PRIMARY KEY,
            note_id TEXT,
            user_id TEXT,
            content TEXT,
            created_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id TEXT PRIMARY KEY,
            note_id TEXT,
            user_id TEXT,
            created_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            note_id TEXT,
            event_type TEXT,
            message TEXT,
            created_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS publish_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note_id TEXT,
            title TEXT,
            author TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_published_note(data):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO notes (id, title, content, author, created_at, likes, comments, heat, status)
        VALUES (?, ?, ?, ?, ?, COALESCE((SELECT likes FROM notes WHERE id=?), 0),
                COALESCE((SELECT comments FROM notes WHERE id=?), 0),
                COALESCE((SELECT heat FROM notes WHERE id=?), 0), 'approved')
    """, (
        data["note_id"], data["title"], data["content"], data.get("author", "guest"),
        data.get("created_at", datetime.now().isoformat()),
        data["note_id"], data["note_id"], data["note_id"]
    ))
    conn.commit()
    conn.close()


def save_publish_log(data):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO publish_logs (note_id, title, author, created_at) VALUES (?, ?, ?, ?)
    """, (
        data["note_id"], data["title"], data.get("author", "guest"),
        data.get("created_at", datetime.now().isoformat())
    ))
    conn.commit()
    conn.close()


def get_notes():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_note(note_id):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    note = cursor.fetchone()
    conn.close()
    return note


def get_comments(note_id):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM comments WHERE note_id = ? ORDER BY created_at DESC", (note_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_like_count(note_id):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM likes WHERE note_id = ?", (note_id,))
    result = cursor.fetchone()
    conn.close()
    return result["count"] if result else 0


def add_comment(note_id, user_id, comment_text):
    import uuid
    conn = _get_connection()
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO comments (id, note_id, user_id, content, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (str(uuid.uuid4()), note_id, str(user_id), comment_text, created_at))
    cursor.execute("UPDATE notes SET comments = comments + 1 WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()


def add_like(note_id, user_id):
    import uuid
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO likes (id, note_id, user_id, created_at)
        VALUES (?, ?, ?, ?)
    """, (str(uuid.uuid4()), note_id, str(user_id), datetime.now().isoformat()))
    cursor.execute("UPDATE notes SET likes = likes + 1 WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()


def update_note_heat(note_id, amount=1):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notes SET heat = heat + ? WHERE id = ?", (amount, note_id))
    conn.commit()
    conn.close()


def delete_note(note_id):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM comments WHERE note_id = ?", (note_id,))
    cursor.execute("DELETE FROM likes WHERE note_id = ?", (note_id,))
    cursor.execute("DELETE FROM notifications WHERE note_id = ?", (note_id,))
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()


def clear_database():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM comments")
    cursor.execute("DELETE FROM likes")
    cursor.execute("DELETE FROM notifications")
    cursor.execute("DELETE FROM publish_logs")
    cursor.execute("DELETE FROM notes")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'publish_logs'")
    conn.commit()
    conn.close()


def add_notification(note_id, event_type, message):
    import uuid
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notifications (id, note_id, event_type, message, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (str(uuid.uuid4()), note_id, event_type, message, datetime.now().isoformat()))
    conn.commit()
    conn.close()