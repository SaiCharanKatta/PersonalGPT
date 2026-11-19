from hosting_config import DATA_DIR
from postgres_backend import DATABASE_URL
from io import BytesIO

import streamlit as st
import sys

if "/content" not in sys.path:
    sys.path.insert(0, "/content")

import database
import auth

st.title("Personal GPT — Admin")
st.caption("Private profile management dashboard")

# -----------------------------------
# AUTHENTICATION
# -----------------------------------


if not st.session_state.get("admin_authenticated", False):

    st.subheader("Admin login")

    with st.form("admin_login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")

    if submitted:
        try:
            if auth.verify_admin_login(username, password):
                st.session_state["admin_authenticated"] = True
                st.session_state["admin_username"] = username.strip().lower()
                st.rerun()
            else:
                st.error(
                    "Nice try! This area is reserved for the admin. "
                    "Looks like you took a wrong turn!"
                )
        except Exception:
            st.error(
                "Nice try! This area is reserved for the admin. "
                "Looks like you took a wrong turn!"
            )

    with st.expander("Forgot username or password?"):
        st.warning(
            "Use your private one-time recovery code. "
            "It can reset the existing administrator account; "
            "it does not create another admin."
        )

        with st.form("admin_recovery_form"):
            recovery_code_input = st.text_input(
                "One-time recovery code",
                type="password"
            )
            recovery_username = st.text_input(
                "New admin username"
            )
            recovery_password = st.text_input(
                "New password",
                type="password"
            )
            recovery_password_confirm = st.text_input(
                "Confirm new password",
                type="password"
            )
            recover = st.form_submit_button("Recover admin account")

        if recover:
            if recovery_password != recovery_password_confirm:
                st.error("The passwords do not match.")
            else:
                try:
                    auth.consume_admin_recovery_code(
                        recovery_code_input,
                        recovery_username,
                        recovery_password
                    )
                    st.success(
                        "Admin credentials updated. "
                        "Please sign in with your new username and password."
                    )
                except Exception as error:
                    st.error(str(error))

    st.stop()


# AUTHENTICATED DASHBOARD
# -----------------------------------

st.success(
    "Authenticated as " +
    st.session_state.get("admin_username", "Admin")
)

# PRIVATE ADMIN AI ASSISTANT
# Existing authentication above protects this workspace.
import admin_ai
admin_ai.render_admin_ai()

if st.button("Log out"):
    st.session_state.pop("admin_authenticated", None)
    st.session_state.pop("admin_username", None)
    st.rerun()


# -----------------------------------

# -----------------------------------
# ADMIN ACCOUNT SETTINGS
# -----------------------------------

st.divider()
with st.expander("Admin account settings"):
    st.caption(
        "Change the username or password of the existing admin account. "
        "No additional admin accounts can be created here."
    )

    with st.form("admin_account_settings"):
        current_username = st.session_state.get("admin_username", "")

        new_username_value = st.text_input(
            "New username (leave blank to keep current)",
            value=""
        )
        new_password_value = st.text_input(
            "New password (leave blank to keep current)",
            type="password"
        )
        confirm_new_password = st.text_input(
            "Confirm new password",
            type="password"
        )

        save_credentials = st.form_submit_button(
            "Update admin credentials"
        )

    if save_credentials:
        if (
            new_password_value
            and new_password_value != confirm_new_password
        ):
            st.error("The passwords do not match.")
        elif not new_username_value and not new_password_value:
            st.warning("Enter a new username or password.")
        else:
            try:
                auth.update_admin_credentials(
                    current_username,
                    new_username=(
                        new_username_value or None
                    ),
                    new_password=(
                        new_password_value or None
                    )
                )

                if new_username_value:
                    st.session_state["admin_username"] = (
                        new_username_value.strip().lower()
                    )

                st.success("Admin credentials updated.")
                st.rerun()

            except Exception as error:
                st.error(str(error))


# DATABASE SUMMARY
# -----------------------------------

st.divider()
st.header("Dashboard overview")

summary = database.get_database_summary()

cols = st.columns(4)

for index, (table, count) in enumerate(summary.items()):
    with cols[index % 4]:
        st.metric(table.replace("_", " ").title(), count)


# -----------------------------------
# PROFILE MANAGEMENT
# -----------------------------------

st.divider()
st.header("Professional profile")

profile = database.get_profile() or {}

with st.form("profile_editor"):

    full_name = st.text_input(
        "Full name",
        value=profile.get("full_name") or ""
    )

    professional_title = st.text_input(
        "Professional title",
        value=profile.get("professional_title") or ""
    )

    professional_summary = st.text_area(
        "Professional summary",
        value=profile.get("professional_summary") or "",
        height=140
    )

    location = st.text_input(
        "Location",
        value=profile.get("location") or ""
    )

    public_email = st.text_input(
        "Public email",
        value=profile.get("public_email") or ""
    )

    email_approved = st.checkbox(
        "Approve email for public display",
        value=bool(profile.get("email_approved"))
    )

    profile_status = st.selectbox(
        "Profile publication status",
        ["draft", "approved", "archived"],
        index=["draft", "approved", "archived"].index(
            profile.get("profile_status")
            if profile.get("profile_status") in
            ["draft", "approved", "archived"]
            else "draft"
        )
    )

    save_profile = st.form_submit_button("Save profile")

    if save_profile:

        if not full_name.strip():
            st.error("Full name cannot be empty.")

        else:
            try:
                database.update_profile({
                    "full_name": full_name.strip(),
                    "professional_title": professional_title.strip(),
                    "professional_summary": professional_summary.strip(),
                    "location": location.strip(),
                    "public_email": public_email.strip() or None,
                    "email_approved": int(email_approved),
                    "profile_status": profile_status
                })

                st.success("Profile saved successfully.")
                st.rerun()

            except Exception as error:
                st.error(f"Could not save profile: {error}")


# -----------------------------------

# -----------------------------------
# PRIVATE DOCUMENT LIBRARY
# -----------------------------------

import hashlib
import re
import uuid
from pathlib import Path
from urllib.parse import quote

PRIVATE_DOCUMENT_DIR = Path(
    str(DATA_DIR / "private_documents")
).resolve()

PRIVATE_DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_DOCUMENT_TYPES = {
    "pdf", "doc", "docx", "png", "jpg", "jpeg", "webp"
}
MAX_DOCUMENT_SIZE = 25 * 1024 * 1024


def store_private_document(original_name, file_bytes, notes=""):

    original_filename = Path(str(original_name)).name

    if not original_filename:
        raise ValueError("Invalid filename.")

    if not file_bytes:
        raise ValueError("The selected file is empty.")

    if len(file_bytes) > MAX_DOCUMENT_SIZE:
        raise ValueError("The file exceeds the 25 MB limit.")

    safe_filename = re.sub(
        r"[^A-Za-z0-9._-]",
        "_",
        original_filename
    )

    extension = Path(safe_filename).suffix.lower().lstrip(".")

    if extension not in ALLOWED_DOCUMENT_TYPES:
        raise ValueError("Unsupported document type.")

    file_hash = hashlib.sha256(file_bytes).hexdigest()

    with database.get_connection() as conn:

        duplicate = conn.execute(
            """
            SELECT id FROM resume_documents
            WHERE file_hash = ?
            LIMIT 1
            """,
            (file_hash,)
        ).fetchone()

        if duplicate:
            raise ValueError("This exact file is already stored.")

        version_row = conn.execute(
            """
            SELECT COALESCE(MAX(version_number), 0)
            FROM resume_documents
            WHERE LOWER(original_filename) = LOWER(?)
            """,
            (original_filename,)
        ).fetchone()

        version_number = int(version_row[0] or 0) + 1

        stored_filename = uuid.uuid4().hex + "_" + safe_filename
        stored_path = (PRIVATE_DOCUMENT_DIR / stored_filename).resolve()

        if PRIVATE_DOCUMENT_DIR not in stored_path.parents:
            raise ValueError("Invalid private storage path.")

        if not DATABASE_URL:
            stored_path.write_bytes(file_bytes)

        try:
            file_column = ", file_bytes" if DATABASE_URL else ""
            file_parameter = ", ?" if DATABASE_URL else ""
            params = (
                original_filename, stored_filename,
                stored_filename if DATABASE_URL else str(stored_path),
                extension, len(file_bytes), file_hash, version_number,
                "pending", str(notes or "").strip() or None,
            )
            if DATABASE_URL:
                params += (file_bytes,)
            conn.execute(
                f"""
                INSERT INTO resume_documents (
                    original_filename, stored_filename, storage_path, file_type,
                    file_size, file_hash, version_number, review_status, notes{file_column}
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?{file_parameter})
                """,
                params,
            )
            conn.commit()

        except Exception:
            if stored_path.exists():
                stored_path.unlink()
            raise

    return version_number


def extract_pdf_text(document_bytes):

    try:
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(document_bytes))
        return "\n\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    except ImportError:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(BytesIO(document_bytes))
            return "\n\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )
        except ImportError:
            return (
                "PDF text extraction requires pypdf. "
                "Run !pip install pypdf in Colab, then rerun the app."
            )


st.divider()
st.header("Private document library")

st.caption(
    "Private files are accessible only after admin authentication. "
    "Uploaded files are not automatically published."
)

with st.expander("Upload files from your computer", expanded=True):

    uploaded_documents = st.file_uploader(
        "Choose PDF, Word documents or images",
        type=sorted(ALLOWED_DOCUMENT_TYPES),
        accept_multiple_files=True,
        key="admin_private_document_uploader"
    )

    upload_notes = st.text_input(
        "Notes (optional)",
        key="private_upload_notes"
    )

    if st.button(
        "Upload selected files",
        type="primary",
        key="upload_private_documents"
    ):

        if not uploaded_documents:
            st.warning("Choose at least one file.")

        else:

            for uploaded in uploaded_documents:

                try:
                    version = store_private_document(
                        uploaded.name,
                        uploaded.getvalue(),
                        upload_notes
                    )

                    st.success(
                        f"{uploaded.name} stored as version {version}."
                    )

                except ValueError as error:
                    st.warning(f"{uploaded.name}: {error}")

                except Exception as error:
                    st.error(
                        f"Could not store {uploaded.name}: "
                        f"{type(error).__name__}"
                    )

            st.rerun()


# Colab-mounted Google Drive browser.
with st.expander("Import from my mounted Google Drive"):

    drive_root = DATA_DIR

    if not drive_root.exists():
        st.warning(
            "Google Drive is not mounted. Mount Drive in Colab first."
        )

    else:

        if st.button(
            "Scan My Drive for supported files",
            key="scan_mounted_drive"
        ):

            found_files = []

            for path in drive_root.rglob("*"):

                if not path.is_file():
                    continue

                try:
                    if PRIVATE_DOCUMENT_DIR in path.resolve().parents:
                        continue

                    if path.suffix.lower().lstrip(".") in ALLOWED_DOCUMENT_TYPES:
                        found_files.append(str(path))

                except (OSError, PermissionError):
                    continue

                if len(found_files) >= 500:
                    break

            st.session_state["mounted_drive_files"] = sorted(found_files)

        drive_files = st.session_state.get("mounted_drive_files", [])

        if drive_files:

            selected_drive_file = st.selectbox(
                "Choose a file from Google Drive",
                drive_files,
                format_func=lambda value: Path(value).name,
                key="selected_mounted_drive_file"
            )

            drive_notes = st.text_input(
                "Import notes (optional)",
                key="mounted_drive_notes"
            )

            if st.button(
                "Import selected Drive file",
                key="import_mounted_drive_file"
            ):

                try:

                    selected_path = Path(selected_drive_file).resolve()

                    if drive_root.resolve() not in selected_path.parents:
                        raise ValueError("Selected file is outside My Drive.")

                    file_bytes = selected_path.read_bytes()

                    version = store_private_document(
                        selected_path.name,
                        file_bytes,
                        drive_notes
                    )

                    st.success(
                        f"Imported {selected_path.name}, version {version}."
                    )
                    st.rerun()

                except ValueError as error:
                    st.warning(str(error))

                except Exception as error:
                    st.error(
                        "Drive import failed: " + type(error).__name__
                    )

        else:
            st.caption(
                "Select Scan My Drive to find supported files."
            )


st.subheader("Stored private documents")

try:

    with database.get_connection() as conn:

        document_rows = conn.execute(
            """
            SELECT *
            FROM resume_documents
            ORDER BY uploaded_at DESC, id DESC
            """
        ).fetchall()

        private_documents = [dict(row) for row in document_rows]

except Exception as error:

    private_documents = []
    st.error("Could not load the private document library.")


if not private_documents:

    st.info("No private documents have been uploaded yet.")

else:

    st.caption(
        f"{len(private_documents)} stored document version(s)."
    )

    for document in private_documents:

        document_id = int(document["id"])
        filename = document["original_filename"]
        version = document.get("version_number") or 1

        with st.expander(f"{filename} — Version {version}"):

            st.write("**File type:**", document.get("file_type", "").upper())
            st.write(
                "**File size:**",
                f'{(document.get("file_size") or 0) / 1024:.1f} KB'
            )
            st.write("**Uploaded:**", document.get("uploaded_at") or "Unknown")
            st.write(
                "**Review status:**",
                document.get("review_status") or "Pending"
            )

            if document.get("notes"):
                st.write("**Notes:**", document["notes"])

            document_path = Path(
                document.get("storage_path") or ""
            ).resolve()

            safe_path = (
                PRIVATE_DOCUMENT_DIR in document_path.parents
                and document_path.is_file()
            )

            document_bytes = None
            if DATABASE_URL:
                try:
                    with database.get_connection() as conn:
                        stored = conn.execute(
                            "SELECT file_bytes FROM resume_documents WHERE id = ?",
                            (document_id,),
                        ).fetchone()
                    if stored:
                        document_bytes = bytes(stored[0])
                except Exception:
                    st.error("The stored file could not be read.")
            elif safe_path:
                try:
                    document_bytes = document_path.read_bytes()
                except OSError:
                    st.error("The stored file could not be read.")

            if document_bytes is not None:

                try:

                    st.download_button(
                        "Download original file",
                        data=document_bytes,
                        file_name=filename,
                        key=f"download_private_{document_id}",
                        use_container_width=True
                    )

                except Exception:
                    st.error("The stored file could not be read.")

            else:
                st.warning(
                    "The file is missing or its path is outside "
                    "the private document folder."
                )

            if str(document.get("file_type") or "").lower() == "pdf":

                if st.button(
                    "Read / extract PDF text",
                    key=f"extract_pdf_{document_id}"
                ):

                    if document_bytes is not None:
                        extracted = extract_pdf_text(document_bytes)
                        st.session_state[
                            f"extracted_pdf_{document_id}"
                        ] = extracted
                    else:
                        st.error("The PDF file is not available.")

                extracted_text = st.session_state.get(
                    f"extracted_pdf_{document_id}"
                )

                if extracted_text is not None:

                    st.text_area(
                        "Extracted PDF text",
                        value=extracted_text,
                        height=240,
                        key=f"pdf_text_display_{document_id}"
                    )

                    st.caption(
                        "This is extracted text for review. It does not "
                        "change your profile or approve any content."
                    )

            st.divider()

            confirm_delete = st.checkbox(
                "I confirm that I want to delete this document version",
                key=f"confirm_delete_document_{document_id}"
            )

            if st.button(
                "Delete this document",
                key=f"delete_private_document_{document_id}",
                disabled=not confirm_delete
            ):

                try:

                    if not DATABASE_URL and not safe_path:
                        raise ValueError(
                            "Deletion blocked: file path is not verified "
                            "inside the private document folder."
                        )

                    if not DATABASE_URL:
                        document_path.unlink()

                    with database.get_connection() as conn:
                        conn.execute(
                            "DELETE FROM resume_documents WHERE id = ?",
                            (document_id,)
                        )
                        conn.commit()

                    st.success("Document version deleted.")
                    st.rerun()

                except Exception as error:
                    st.error(
                        "Could not delete document: "
                        + str(error)
                    )


st.caption(
    "Private documents are never automatically published or included "
    "in the public chatbot's profile context."
)


# -----------------------------------

# -----------------------------------
# CONTENT APPROVAL — CONTENT MANAGER
# -----------------------------------

st.divider()
st.header("Content management")

with st.expander("＋ Add Section"):
    st.caption("Create a new portfolio section without editing Python code.")
    new_section_name=st.text_input("Section name", key="new_section_name")
    new_section_description=st.text_area("What should this section contain?", key="new_section_description")
    if st.button("Create section draft", key="create_section_draft"):
        if new_section_name.strip():
            st.session_state.setdefault("custom_sections", []).append({"name": new_section_name.strip(), "description": new_section_description.strip()})
            st.success(f"Section draft created: {new_section_name.strip()}. Define its fields through the Admin AI chat.")
        else:
            st.warning("Enter a section name first.")


st.caption(
    "Add, edit, delete and approve professional information. "
    "New entries are always saved as drafts."
)

SKILL_CATEGORIES = {
    "Programming": ["Java", "Python"],
    "Web Development": ["HTML", "CSS", "PHP", "WordPress"],
    "Databases": ["Oracle SQL", "MySQL", "phpMyAdmin"],
    "AI & Machine Learning": [
        "Machine Learning", "Convolutional Neural Networks"
    ],
    "Hosting & Server Administration": [
        "cPanel", "WHM", "Linux", "VPS Support",
        "SSH / PuTTY", "FileZilla"
    ],
    "Networking & DNS": [
        "DNS Management", "Networking Fundamentals",
        "Email Routing", "MX Records"
    ],
    "Security & Web Protection": [
        "SSL", "WAF / CDN", "SPF / DKIM / DMARC"
    ],
    "Business & Support Platforms": [
        "Salesforce", "Jira", "Confluence Cloud",
        "Slack", "Microsoft Teams", "Microsoft Excel"
    ],
    "Troubleshooting & Diagnostics": [
        "Splunk", "cURL", "Ping / Traceroute"
    ]
}

TABLES = [
    ("education", "Education"),
    ("experience", "Experience"),
    ("skills", "Skills"),
    ("projects", "Projects"),
    ("languages", "Languages"),
    ("certifications", "Certifications"),
    ("achievements", "Achievements")
]

FIELD_LABELS = {
    "qualification": "Qualification",
    "institution": "Institution",
    "specialization": "Specialization",
    "start_year": "Start year",
    "end_year": "End year",
    "company": "Company",
    "job_title": "Job title",
    "employment_type": "Employment type",
    "location": "Location",
    "start_date": "Start date",
    "end_date": "End date",
    "is_current": "Currently employed",
    "description": "Description",
    "skill_name": "Skill name",
    "category": "Category",
    "project_name": "Project name",
    "technologies": "Technologies",
    "project_type": "Project type",
    "language_name": "Language",
    "proficiency": "Proficiency",
    "certification_name": "Certification name",
    "issuing_organization": "Issuing organization",
    "issue_date": "Issue date",
    "credential_url": "Credential URL",
    "title": "Title",
    "achievement_date": "Achievement date"
}

LONG_FIELDS = {"description", "technologies"}
OMIT_FIELDS = {"id", "status", "sort_order", "proficiency"}

def render_record_field(field, value, key, table):
    label = FIELD_LABELS.get(
        field, field.replace("_", " ").title()
    )

    if field == "is_current":
        return int(st.checkbox(
            label,
            value=bool(value),
            key=key
        ))

    if field == "category" and table == "skills":
        options = list(SKILL_CATEGORIES.keys())
        current = str(value or "Programming")
        if current not in options:
            options.append(current)
        return st.selectbox(
            label, options,
            index=options.index(current),
            key=key
        )

    if field in LONG_FIELDS:
        return st.text_area(
            label,
            value=str(value or ""),
            height=110,
            key=key
        )

    return st.text_input(
        label,
        value=str(value or ""),
        key=key
    )

def default_skill_category(skill_name):
    for category, names in SKILL_CATEGORIES.items():
        if skill_name in names:
            return category
    return "Programming"

for table, label in TABLES:

    records = database.get_records(table)

    # A bordered container is used instead of nested expanders.
    with st.container(border=True):
        st.subheader(f"{label} ({len(records)})")

        # Add new record
        with st.expander("＋"):
            with st.form(f"add_record_{table}"):

                new_data = {}

                if table == "education":
                    fields = [
                        "qualification", "institution",
                        "specialization", "start_year", "end_year"
                    ]
                elif table == "experience":
                    fields = [
                        "company", "job_title", "employment_type",
                        "location", "start_date", "end_date",
                        "is_current", "description"
                    ]
                elif table == "skills":
                    fields = ["skill_name", "category"]
                elif table == "projects":
                    fields = [
                        "project_name", "description",
                        "technologies", "project_type"
                    ]
                elif table == "languages":
                    fields = ["language_name", "proficiency"]
                elif table == "certifications":
                    fields = [
                        "certification_name", "issuing_organization",
                        "issue_date", "credential_url"
                    ]
                else:
                    fields = [
                        "title", "description", "achievement_date"
                    ]

                for field in fields:
                    initial = (
                        "Programming"
                        if field == "category" and table == "skills"
                        else ""
                    )
                    new_data[field] = render_record_field(
                        field, initial,
                        f"new_{table}_{field}", table
                    )

                add_submitted = st.form_submit_button(
                    f"Save new {label[:-1] if label.endswith('s') else label}"
                )

            if add_submitted:
                try:
                    if table == "skills":
                        skill_name = str(
                            new_data.get("skill_name") or ""
                        ).strip()
                        if not skill_name:
                            raise ValueError("Skill name is required.")

                        new_data["proficiency"] = "Not specified"
                        new_data["sort_order"] = (
                            len(records) + 1
                        )

                    new_data["status"] = "draft"
                    database.add_record(table, new_data)

                    st.success(
                        "New record saved as draft."
                    )
                    st.rerun()

                except Exception as error:
                    st.error(f"Could not add record: {error}")

        # Bulk approval controls
        if records:
            approve_all_col, draft_all_col = st.columns(2)

            with approve_all_col:
                if st.button(
                    f"Approve all {label.lower()}",
                    key=f"approve_all_{table}",
                    use_container_width=True
                ):
                    for record in records:
                        database.update_record(
                            table,
                            int(record["id"]),
                            {"status": "approved"}
                        )
                    st.success(f"All {label.lower()} approved.")
                    st.rerun()

            with draft_all_col:
                if st.button(
                    f"Move all to draft",
                    key=f"draft_all_{table}",
                    use_container_width=True
                ):
                    for record in records:
                        database.update_record(
                            table,
                            int(record["id"]),
                            {"status": "draft"}
                        )
                    st.info(f"All {label.lower()} moved to draft.")
                    st.rerun()

        if not records:
            st.info(f"No {label.lower()} records yet.")

        # Skill category approval
        if table == "skills" and records:
            st.markdown("**Approve a complete skill category**")

            for category in SKILL_CATEGORIES:
                category_records = [
                    r for r in records
                    if (r.get("category") or "") == category
                ]

                if not category_records:
                    continue

                pending = sum(
                    1 for r in category_records
                    if r.get("status") != "approved"
                )

                category_col, count_col, button_col = st.columns(
                    [3, 1, 2]
                )

                category_col.write(category)
                count_col.write(f"{len(category_records)} skills")

                if button_col.button(
                    "Approve category",
                    key=f"approve_skill_category_{category}",
                    disabled=(pending == 0),
                    use_container_width=True
                ):
                    for record in category_records:
                        database.update_record(
                            "skills",
                            int(record["id"]),
                            {"status": "approved"}
                        )
                    st.success(f"{category} approved.")
                    st.rerun()

        # Existing records
        for record in records:
            record_id = int(record["id"])
            status = record.get("status") or "draft"

            if table == "skills":
                heading = (
                    str(record.get("skill_name") or "Skill")
                    + " — "
                    + str(record.get("category") or "Other")
                )
            elif table == "education":
                heading = str(
                    record.get("qualification") or "Education"
                )
            elif table == "experience":
                heading = str(
                    record.get("job_title") or "Experience"
                )
            elif table == "projects":
                heading = str(
                    record.get("project_name") or "Project"
                )
            elif table == "languages":
                heading = str(
                    record.get("language_name") or "Language"
                )
            elif table == "certifications":
                heading = str(
                    record.get("certification_name") or "Certification"
                )
            else:
                heading = str(
                    record.get("title") or "Achievement"
                )

            with st.expander(
                f"{heading}  ·  #{record_id}  ·  {status.upper()}"
            ):
                fields = [
                    key for key in record.keys()
                    if key not in OMIT_FIELDS
                ]

                with st.form(f"edit_{table}_{record_id}"):
                    edited = {}

                    for field in fields:
                        edited[field] = render_record_field(
                            field,
                            record.get(field),
                            f"edit_{table}_{record_id}_{field}",
                            table
                        )

                    save_edit = st.form_submit_button(
                        "Save changes"
                    )

                if save_edit:
                    try:
                        database.update_record(
                            table, record_id, edited
                        )
                        st.success(
                            "Changes saved. Approval status unchanged."
                        )
                        st.rerun()
                    except Exception as error:
                        st.error(f"Could not save: {error}")

                approve_col, draft_col = st.columns(2)

                with approve_col:
                    if st.button(
                        "Approve",
                        key=f"approve_{table}_{record_id}",
                        use_container_width=True,
                        disabled=(status == "approved")
                    ):
                        database.update_record(
                            table, record_id,
                            {"status": "approved"}
                        )
                        st.rerun()

                with draft_col:
                    if st.button(
                        "Move to draft",
                        key=f"draft_{table}_{record_id}",
                        use_container_width=True,
                        disabled=(status == "draft")
                    ):
                        database.update_record(
                            table, record_id,
                            {"status": "draft"}
                        )
                        st.rerun()

                confirm_delete = st.checkbox(
                    "I confirm that I want to delete this record",
                    key=f"confirm_delete_{table}_{record_id}"
                )

                if st.button(
                    "Delete record",
                    key=f"delete_{table}_{record_id}",
                    disabled=not confirm_delete
                ):
                    try:
                        database.delete_record(table, record_id)
                        st.success("Record deleted.")
                        st.rerun()
                    except Exception as error:
                        st.error(f"Could not delete record: {error}")




# CONTACT ENQUIRIES
# -----------------------------------

st.divider()
st.header("Contact enquiries")

messages = database.get_records("contact_messages")

if messages:

    messages = sorted(
        messages,
        key=lambda item: (
            int(item.get("is_pinned") or 0),
            str(item.get("submitted_at") or "")
        ),
        reverse=True
    )

    for message in messages:

        message_id = int(message["id"])
        visitor_name = message.get("visitor_name") or "Visitor"
        visitor_email = message.get("visitor_email") or ""
        subject = message.get("subject") or "(No subject)"
        pinned = bool(message.get("is_pinned"))

        pin_label = "📌 " if pinned else ""

        with st.expander(
            f"{pin_label}{visitor_name} — {subject} — "
            f"{message.get('submitted_at') or 'Date unavailable'}"
        ):

            st.write("**From:**", visitor_name)
            st.write("**Email:**", visitor_email)
            st.write("**Subject:**", subject)
            st.write("**Message:**")
            st.write(message.get("message") or "")

            st.caption(
                "Status: "
                + str(message.get("submission_status") or "new")
            )

            pin_col, email_col, delete_col = st.columns(3)

            with pin_col:

                if st.button(
                    "Unpin" if pinned else "Pin enquiry",
                    key=f"pin_enquiry_{message_id}",
                    use_container_width=True
                ):

                    database.update_record(
                        "contact_messages",
                        message_id,
                        {"is_pinned": 0 if pinned else 1}
                    )

                    st.rerun()

            with email_col:

                gmail_url = (
                    "https://mail.google.com/mail/?view=cm&fs=1"
                    "&to=" + quote(visitor_email, safe="")
                    + "&su=" + quote(subject, safe="")
                )

                st.link_button(
                    "Draft in Gmail",
                    gmail_url,
                    use_container_width=True
                )

            with delete_col:

                confirm_delete_enquiry = st.checkbox(
                    "Confirm delete",
                    key=f"confirm_delete_enquiry_{message_id}"
                )

                if st.button(
                    "Delete enquiry",
                    key=f"delete_enquiry_{message_id}",
                    disabled=not confirm_delete_enquiry,
                    use_container_width=True
                ):

                    with database.get_connection() as conn:
                        conn.execute(
                            "DELETE FROM contact_messages WHERE id = ?",
                            (message_id,)
                        )
                        conn.commit()

                    st.success("Enquiry deleted.")
                    st.rerun()

else:

    st.info("No contact enquiries received yet.")


st.divider()
st.caption("Personal GPT — Private administration area")
