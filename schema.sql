CREATE TABLE profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    full_name TEXT NOT NULL,
    professional_title TEXT,
    professional_summary TEXT,
    public_email TEXT,
    email_approved INTEGER DEFAULT 0,
    location TEXT,
    profile_status TEXT DEFAULT 'draft',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE education (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qualification TEXT NOT NULL,
    institution TEXT,
    specialization TEXT,
    start_year TEXT,
    end_year TEXT,
    status TEXT DEFAULT 'draft',
    sort_order INTEGER DEFAULT 0
);
CREATE TABLE experience (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    job_title TEXT,
    employment_type TEXT,
    location TEXT,
    start_date TEXT,
    end_date TEXT,
    is_current INTEGER DEFAULT 0,
    description TEXT,
    status TEXT DEFAULT 'draft',
    sort_order INTEGER DEFAULT 0
);
CREATE TABLE skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL,
    category TEXT,
    proficiency TEXT,
    status TEXT DEFAULT 'draft',
    sort_order INTEGER DEFAULT 0,
    UNIQUE(skill_name, category)
);
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    description TEXT,
    technologies TEXT,
    project_type TEXT,
    status TEXT DEFAULT 'draft',
    sort_order INTEGER DEFAULT 0
);
CREATE TABLE languages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language_name TEXT NOT NULL UNIQUE,
    proficiency TEXT,
    status TEXT DEFAULT 'draft'
);
CREATE TABLE certifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    certification_name TEXT NOT NULL,
    issuing_organization TEXT,
    issue_date TEXT,
    credential_url TEXT,
    status TEXT DEFAULT 'draft'
);
CREATE TABLE achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    achievement_date TEXT,
    status TEXT DEFAULT 'draft'
);
CREATE TABLE resume_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_filename TEXT NOT NULL,
    stored_filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    file_type TEXT,
    file_size INTEGER,
    file_hash TEXT,
    version_number INTEGER,
    uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
    review_status TEXT DEFAULT 'pending',
    notes TEXT
);
CREATE TABLE admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE contact_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visitor_name TEXT NOT NULL,
    visitor_email TEXT NOT NULL,
    message TEXT NOT NULL,
    submission_status TEXT DEFAULT 'new',
    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP
, subject TEXT, is_pinned INTEGER NOT NULL DEFAULT 0);
CREATE TABLE admin_recovery (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                used_at TEXT
            );
CREATE TABLE site_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE portfolio_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_key TEXT NOT NULL UNIQUE,
    section_title TEXT NOT NULL,
    section_type TEXT NOT NULL DEFAULT 'content',
    is_visible INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0,
    configuration_json TEXT DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'approved',
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE profile_custom_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_key TEXT NOT NULL,
    field_label TEXT NOT NULL,
    field_value TEXT,
    sort_order INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE portfolio_intro (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_key TEXT NOT NULL UNIQUE,
    heading TEXT,
    body TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE portfolio_highlights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    sort_order INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE admin_ai_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_text TEXT NOT NULL,
    proposal_json TEXT NOT NULL,
    preview_text TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TEXT,
    reviewed_by TEXT,
    applied_at TEXT
);
CREATE TABLE admin_ai_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER,
    action TEXT NOT NULL,
    details_json TEXT,
    performed_by TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);