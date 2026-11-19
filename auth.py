
import sqlite3
import hashlib
import secrets
import hmac
import re
from datetime import datetime, timezone

from database import get_connection


# Password hashing configuration
HASH_ALGORITHM = "sha256"
HASH_ITERATIONS = 600000


def hash_password(password):

    if not isinstance(password, str) or len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")

    salt = secrets.token_bytes(32)

    password_hash = hashlib.pbkdf2_hmac(
        HASH_ALGORITHM,
        password.encode("utf-8"),
        salt,
        HASH_ITERATIONS
    )

    return (
        f"pbkdf2_{HASH_ALGORITHM}"
        f"${HASH_ITERATIONS}"
        f"${salt.hex()}"
        f"${password_hash.hex()}"
    )


def verify_password(password, stored_hash):

    try:
        algorithm, iterations, salt_hex, hash_hex = stored_hash.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)

        actual_hash = hashlib.pbkdf2_hmac(
            HASH_ALGORITHM,
            password.encode("utf-8"),
            salt,
            int(iterations)
        )

        return hmac.compare_digest(actual_hash, expected_hash)

    except (ValueError, TypeError, AttributeError):
        return False


def create_first_admin(username, password):

    username = username.strip().lower()

    if not re.fullmatch(r"[a-z0-9_.-]{3,40}", username):
        raise ValueError(
            "Username must be 3–40 characters and use only "
            "letters, numbers, dots, underscores or hyphens."
        )

    password_hash = hash_password(password)

    with get_connection() as conn:

        existing = conn.execute(
            "SELECT COUNT(*) FROM admin_users"
        ).fetchone()[0]

        if existing > 0:
            raise ValueError(
                "An admin account already exists. "
                "First-admin setup is disabled."
            )

        conn.execute(
            """
            INSERT INTO admin_users (
                username,
                password_hash,
                is_active,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                username,
                password_hash,
                1,
                datetime.now(timezone.utc).isoformat()
            )
        )

        conn.commit()

    return True


def verify_admin_login(username, password):

    username = username.strip().lower()

    with get_connection() as conn:

        admin = conn.execute(
            """
            SELECT id, password_hash, is_active
            FROM admin_users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

    if not admin:
        return False

    if admin["is_active"] != 1:
        return False

    return verify_password(password, admin["password_hash"])


def get_admin_count():

    with get_connection() as conn:

        return conn.execute(
            "SELECT COUNT(*) FROM admin_users"
        ).fetchone()[0]


# --------------------------------------------------
# ONE-TIME ADMIN RECOVERY
# --------------------------------------------------

def consume_admin_recovery_code(code, new_username, new_password):
    code = str(code or "").strip()
    new_username = str(new_username or "").strip().lower()

    if not code:
        raise ValueError("Recovery code is required.")

    if not re.fullmatch(r"[a-z0-9_.-]{3,40}", new_username):
        raise ValueError(
            "Username must be 3–40 characters and use "
            "letters, numbers, dots, underscores or hyphens."
        )

    password_hash = hash_password(new_password)
    code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()

    with get_connection() as conn:
        recovery = conn.execute(
            """
            SELECT id FROM admin_recovery
            WHERE code_hash = ? AND used_at IS NULL
            ORDER BY id DESC LIMIT 1
            """,
            (code_hash,)
        ).fetchone()

        if not recovery:
            raise ValueError(
                "Recovery code is invalid or has already been used."
            )

        admin = conn.execute(
            "SELECT id FROM admin_users WHERE is_active = 1"
        ).fetchone()

        if not admin:
            raise ValueError("No active administrator was found.")

        conn.execute(
            """
            UPDATE admin_users
            SET username = ?, password_hash = ?
            WHERE id = ?
            """,
            (new_username, password_hash, admin["id"])
        )

        conn.execute(
            """
            UPDATE admin_recovery
            SET used_at = ?
            WHERE id = ?
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                recovery["id"]
            )
        )

        conn.commit()

    return True


def update_admin_credentials(current_username, new_username=None,
                              new_password=None):
    current_username = str(current_username or "").strip().lower()

    if new_username is not None:
        new_username = str(new_username).strip().lower()

        if not re.fullmatch(r"[a-z0-9_.-]{3,40}", new_username):
            raise ValueError(
                "Username must be 3–40 characters and use "
                "letters, numbers, dots, underscores or hyphens."
            )

    password_hash = (
        hash_password(new_password)
        if new_password else None
    )

    with get_connection() as conn:
        admin = conn.execute(
            """
            SELECT id FROM admin_users
            WHERE username = ? AND is_active = 1
            """,
            (current_username,)
        ).fetchone()

        if not admin:
            raise ValueError("Admin account was not found.")

        if new_username is not None:
            conn.execute(
                "UPDATE admin_users SET username = ? WHERE id = ?",
                (new_username, admin["id"])
            )

        if password_hash is not None:
            conn.execute(
                "UPDATE admin_users SET password_hash = ? WHERE id = ?",
                (password_hash, admin["id"])
            )

        conn.commit()

    return True
