from postgres_backend import DATABASE_URL, PostgresConnection
from hosting_config import DB_FILE, DATA_DIR

import sqlite3
import json
from datetime import datetime, timezone

DB_PATH = str(DB_FILE)


# --------------------------------------------------
# ALLOWED DATABASE TABLES AND COLUMNS
# --------------------------------------------------

TABLE_COLUMNS = {
    "profile": {
        "full_name", "professional_title", "professional_summary",
        "public_email", "email_approved", "location",
        "profile_status"
    },
    "education": {
        "qualification", "institution", "specialization",
        "start_year", "end_year", "status", "sort_order"
    },
    "experience": {
        "company", "job_title", "employment_type", "location",
        "start_date", "end_date", "is_current", "description",
        "status", "sort_order"
    },
    "skills": {
        "skill_name", "category", "proficiency", "status",
        "sort_order"
    },
    "projects": {
        "project_name", "description", "technologies",
        "project_type", "status", "sort_order"
    },
    "languages": {
        "language_name", "proficiency", "status"
    },
    "certifications": {
        "certification_name", "issuing_organization",
        "issue_date", "credential_url", "status"
    },
    "achievements": {
        "title", "description", "achievement_date", "status"
    },
    "resume_documents": {
        "original_filename", "stored_filename", "storage_path",
        "file_type", "file_size", "file_hash", "version_number",
        "uploaded_at", "review_status", "notes"
    },
    "admin_users": {
        "username", "password_hash", "is_active", "created_at"
    },
    "contact_messages": {
        "visitor_name", "visitor_email", "subject", "message",
        "submission_status", "submitted_at", "is_pinned"
    }
}


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def insert_id(conn, query, params):
    if isinstance(conn, PostgresConnection):
        return conn.insert_id(query, params)
    return conn.execute(query, params).lastrowid


def ensure_site_settings_table():
    with get_connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS site_settings (setting_key TEXT PRIMARY KEY, setting_value TEXT NOT NULL)")

def get_custom_sections():
    ensure_site_settings_table()
    with get_connection() as conn:
        row=conn.execute("SELECT setting_value FROM site_settings WHERE setting_key = ?", ("custom_sections",)).fetchone()
    if not row: return []
    raw=row[0] if not isinstance(row, dict) else row.get("setting_value")
    try: return json.loads(raw) if raw else []
    except (TypeError, ValueError): return []

def save_custom_section(name, description):
    sections=get_custom_sections()
    sections.append({"name": name.strip(), "description": description.strip(), "status": "draft"})
    payload=json.dumps(sections, ensure_ascii=False)
    with get_connection() as conn:
        conn.execute("INSERT INTO site_settings (setting_key, setting_value) VALUES (?, ?) ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value", ("custom_sections", payload))
    return sections[-1]

def get_connection():
    if DATABASE_URL:
        return PostgresConnection()
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# --------------------------------------------------
# PROFILE
# --------------------------------------------------

def get_profile():
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM profile WHERE id = 1"
        ).fetchone()

        return dict(row) if row else None


def update_profile(fields):
    if not fields:
        raise ValueError("No profile fields supplied.")

    allowed = TABLE_COLUMNS["profile"]

    invalid = set(fields.keys()) - allowed
    if invalid:
        raise ValueError(f"Invalid profile fields: {invalid}")

    columns = list(fields.keys())

    assignments = ", ".join(
        f'"{column}" = ?' for column in columns
    )

    values = [fields[column] for column in columns]

    values.append(
        datetime.now(timezone.utc).isoformat()
    )

    with get_connection() as conn:
        conn.execute(
            f"""
            UPDATE profile
            SET {assignments}, updated_at = ?
            WHERE id = 1
            """,
            values
        )

        conn.commit()

    return True


# --------------------------------------------------
# GENERAL RECORD RETRIEVAL
# --------------------------------------------------

def get_records(table, approved_only=False):

    if table not in TABLE_COLUMNS:
        raise ValueError("Table is not permitted.")

    query = f'SELECT * FROM "{table}"'
    params = []

    if approved_only:
        if table == "profile":
            query += " WHERE profile_status = ?"
            params.append("approved")

        elif "status" in TABLE_COLUMNS[table]:
            query += " WHERE status = ?"
            params.append("approved")

        elif table == "resume_documents":
            query += " WHERE review_status = ?"
            params.append("approved")

        else:
            return []

    if "sort_order" in TABLE_COLUMNS[table]:
        query += " ORDER BY sort_order, id"
    else:
        query += " ORDER BY id"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

        return [dict(row) for row in rows]


# --------------------------------------------------
# PUBLIC PROFILE DATA
# Only approved information is returned.
# Private documents and admin data are excluded.
# --------------------------------------------------

def get_public_profile():

    profile = get_profile()

    if not profile:
        return None

    if profile.get("profile_status") != "approved":
        return None

    public_data = {
        "full_name": profile.get("full_name"),
        "professional_title": profile.get("professional_title"),
        "professional_summary": profile.get("professional_summary"),
        "location": profile.get("location")
    }

    if profile.get("email_approved") and profile.get("public_email"):
        public_data["public_email"] = profile["public_email"]

    public_tables = [
        "education",
        "experience",
        "skills",
        "projects",
        "languages",
        "certifications",
        "achievements"
    ]

    for table in public_tables:
        public_data[table] = get_records(
            table,
            approved_only=True
        )

    return public_data


# --------------------------------------------------
# ADD A RECORD
# --------------------------------------------------

def add_record(table, data):

    if table not in TABLE_COLUMNS:
        raise ValueError("Table is not permitted.")

    if not isinstance(data, dict) or not data:
        raise ValueError("Valid record data is required.")

    invalid = set(data.keys()) - TABLE_COLUMNS[table]

    if invalid:
        raise ValueError(f"Invalid fields: {invalid}")

    columns = list(data.keys())

    column_names = ", ".join(
        f'"{column}"' for column in columns
    )

    placeholders = ", ".join(["?"] * len(columns))

    values = [data[column] for column in columns]

    with get_connection() as conn:
        record_id = insert_id(conn,
            f"""
            INSERT INTO "{table}" ({column_names})
            VALUES ({placeholders})
            """,
            values
        )

        conn.commit()

        return record_id


# --------------------------------------------------
# UPDATE A RECORD
# --------------------------------------------------

def update_record(table, record_id, fields):

    if table not in TABLE_COLUMNS:
        raise ValueError("Table is not permitted.")

    if not fields:
        raise ValueError("No update fields supplied.")

    invalid = set(fields.keys()) - TABLE_COLUMNS[table]

    if invalid:
        raise ValueError(f"Invalid fields: {invalid}")

    columns = list(fields.keys())

    assignments = ", ".join(
        f'"{column}" = ?' for column in columns
    )

    values = [fields[column] for column in columns]
    values.append(record_id)

    with get_connection() as conn:
        cursor = conn.execute(
            f"""
            UPDATE "{table}"
            SET {assignments}
            WHERE id = ?
            """,
            values
        )

        conn.commit()

        return cursor.rowcount > 0


# --------------------------------------------------
# DELETE A RECORD
# --------------------------------------------------

def delete_record(table, record_id):

    if table not in TABLE_COLUMNS:
        raise ValueError("Table is not permitted.")

    with get_connection() as conn:
        cursor = conn.execute(
            f'DELETE FROM "{table}" WHERE id = ?',
            (record_id,)
        )

        conn.commit()

        return cursor.rowcount > 0


# --------------------------------------------------
# CONTACT FORM
# --------------------------------------------------

def save_contact_message(name, email, message, subject=""):

    name = str(name).strip()
    email = str(email).strip()
    subject = str(subject or "").strip()
    message = str(message).strip()

    if not name or not email or not message:
        raise ValueError("Name, email and message are required.")

    if len(name) > 150 or len(email) > 254:
        raise ValueError("Name or email exceeds the allowed length.")

    if len(subject) > 200 or len(message) > 10000:
        raise ValueError("Subject or message exceeds the allowed length.")

    submitted_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        record_id = insert_id(conn,
            """
            INSERT INTO contact_messages (
                visitor_name,
                visitor_email,
                subject,
                message,
                submission_status,
                submitted_at,
                is_pinned
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                email,
                subject,
                message,
                "new",
                submitted_at,
                0
            )
        )

        conn.commit()
        return record_id



# ================================================================
# PERSONAL_GPT_APPROVED_PUBLIC_DATA_EXTENSION
# Shared approved portfolio data for public portfolio and chatbot.
# Private documents, admin accounts and recovery data are excluded.
# ================================================================

_original_get_public_profile = get_public_profile


def get_public_profile():
    public_data = _original_get_public_profile()

    if not isinstance(public_data, dict):
        return public_data

    conn = get_connection()

    try:
        # About Me — only approved content.
        public_data["portfolio_intro"] = [
            dict(row)
            for row in conn.execute(
                """
                SELECT section_key, heading, body
                FROM portfolio_intro
                WHERE status='approved'
                ORDER BY id
                """
            ).fetchall()
        ]

        # Public sections — only sections marked visible.
        public_data["portfolio_sections"] = [
            dict(row)
            for row in conn.execute(
                """
                SELECT section_key, section_title, section_type,
                       is_visible, sort_order, configuration_json
                FROM portfolio_sections
                WHERE is_visible=1
                ORDER BY sort_order, id
                """
            ).fetchall()
        ]

        # Approved highlights only.
        public_data["portfolio_highlights"] = [
            dict(row)
            for row in conn.execute(
                """
                SELECT title, description, icon, sort_order
                FROM portfolio_highlights
                WHERE status='approved'
                ORDER BY sort_order, id
                """
            ).fetchall()
        ]

        # Approved custom profile fields only.
        public_data["custom_fields"] = [
            dict(row)
            for row in conn.execute(
                """
                SELECT field_key, field_label, field_value, sort_order
                FROM profile_custom_fields
                WHERE status='approved'
                ORDER BY sort_order, id
                """
            ).fetchall()
        ]

        # Theme is a public presentation setting.
        theme_row = conn.execute(
            """
            SELECT setting_value
            FROM site_settings
            WHERE setting_key='theme'
            LIMIT 1
            """
        ).fetchone()

        public_data["theme"] = (
            theme_row["setting_value"]
            if theme_row else "dark"
        )

        return public_data

    finally:
        conn.close()

def get_database_summary():
    """Return record counts for the admin dashboard."""
    tables = (
        "profile", "education", "experience", "skills", "projects",
        "languages", "certifications", "achievements", "resume_documents",
        "admin_users", "contact_messages",
    )
    conn = get_connection()
    try:
        return {table: conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                for table in tables}
    finally:
        conn.close()


def set_custom_section_status(index, status):
    sections = get_custom_sections()
    if 0 <= index < len(sections):
        sections[index]["status"] = status
        payload = json.dumps(sections, ensure_ascii=False)
        with get_connection() as conn:
            conn.execute("INSERT INTO site_settings (setting_key, setting_value) VALUES (?, ?) ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value", ("custom_sections", payload))
    return sections
