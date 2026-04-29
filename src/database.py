import hashlib
import hmac
import os
import sqlite3
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "users.db"))


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            password_hash TEXT,
            salt TEXT,
            created_at TEXT
        )"""
    )

    existing_columns = {
        row["name"] for row in c.execute("PRAGMA table_info(users)").fetchall()
    }
    migrations = {
        "password": "ALTER TABLE users ADD COLUMN password TEXT",
        "password_hash": "ALTER TABLE users ADD COLUMN password_hash TEXT",
        "salt": "ALTER TABLE users ADD COLUMN salt TEXT",
        "created_at": "ALTER TABLE users ADD COLUMN created_at TEXT",
    }
    for column, sql in migrations.items():
        if column not in existing_columns:
            c.execute(sql)

    conn.commit()
    conn.close()


def _legacy_hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()


def _hash_password(password, salt=None):
    salt = salt or os.urandom(16).hex()
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000
    ).hex()
    return salt, password_hash


def add_user(username, password):
    username = (username or "").strip()
    if not username or not password:
        return False

    init_db()
    salt, password_hash = _hash_password(password)
    conn = _connect()
    try:
        conn.execute(
            """INSERT INTO users
               (username, password, password_hash, salt, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                username,
                None,
                password_hash,
                salt,
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_user(username, password):
    username = (username or "").strip()
    if not username or not password:
        return False

    init_db()
    conn = _connect()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not user:
        conn.close()
        return False

    if user["password_hash"] and user["salt"]:
        _, candidate_hash = _hash_password(password, user["salt"])
        conn.close()
        return hmac.compare_digest(candidate_hash, user["password_hash"])

    legacy_password = user["password"]
    is_legacy_match = legacy_password and hmac.compare_digest(
        _legacy_hash_password(password), legacy_password
    )
    if is_legacy_match:
        salt, password_hash = _hash_password(password)
        conn.execute(
            "UPDATE users SET password = NULL, password_hash = ?, salt = ? WHERE username = ?",
            (password_hash, salt, username),
        )
        conn.commit()

    conn.close()
    return bool(is_legacy_match)
