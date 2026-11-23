-- NYC Career Launch Tracker | Brett Dowling | Deliverable 3
-- SQLite 3.37+ (STRICT tables). Run outside any existing transaction.
-- WARNING: rebuilding removes this project's existing tables and data.
PRAGMA foreign_keys = ON;
BEGIN IMMEDIATE;

DROP VIEW IF EXISTS application_overview;
DROP TABLE IF EXISTS application_contacts;
DROP TABLE IF EXISTS interviews;
DROP TABLE IF EXISTS application_status_history;
DROP TABLE IF EXISTS applications;
DROP TABLE IF EXISTS contacts;
DROP TABLE IF EXISTS posting_skills;
DROP TABLE IF EXISTS user_skills;
DROP TABLE IF EXISTS job_postings;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    email TEXT NOT NULL COLLATE NOCASE UNIQUE
        CHECK (email = trim(email) AND email LIKE '%_@_%._%')
) STRICT;

CREATE TABLE companies (
    company_id INTEGER PRIMARY KEY,
    company_name TEXT NOT NULL CHECK (length(trim(company_name)) > 0),
    industry TEXT,
    hq_borough TEXT CHECK (hq_borough IN
        ('Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island')),
    company_size TEXT CHECK (company_size IN
        ('1-10', '11-50', '51-200', '201-500', '501-1000', '1001+'))
) STRICT;

CREATE TABLE skills (
    skill_id INTEGER PRIMARY KEY,
    skill_name TEXT NOT NULL COLLATE NOCASE UNIQUE
        CHECK (length(trim(skill_name)) > 0 AND skill_name = trim(skill_name))
) STRICT;

CREATE TABLE job_postings (
    posting_id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(company_id) ON DELETE RESTRICT,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    role_type TEXT NOT NULL CHECK (role_type IN
        ('Software Engineering', 'Data Analytics', 'Data Science', 'IT Support', 'Product')),
    location TEXT NOT NULL CHECK (length(trim(location)) > 0),
    salary_min INTEGER CHECK (salary_min >= 0),
    salary_max INTEGER CHECK (salary_max >= 0),
    posting_status TEXT NOT NULL DEFAULT 'open'
        CHECK (posting_status IN ('open', 'closed', 'paused')),
    posting_url TEXT,
    posted_date TEXT CHECK (posted_date IS NULL OR
        (length(posted_date) = 10 AND date(posted_date, '+0 days') IS NOT NULL
         AND date(posted_date, '+0 days') = posted_date)),
    CHECK (salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max)
) STRICT;

CREATE TABLE user_skills (
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    skill_id INTEGER NOT NULL REFERENCES skills(skill_id) ON DELETE RESTRICT,
    proficiency_level TEXT NOT NULL
        CHECK (proficiency_level IN ('beginner', 'intermediate', 'advanced')),
    PRIMARY KEY (user_id, skill_id)
) STRICT;

CREATE TABLE posting_skills (
    posting_id INTEGER NOT NULL REFERENCES job_postings(posting_id) ON DELETE RESTRICT,
    skill_id INTEGER NOT NULL REFERENCES skills(skill_id) ON DELETE RESTRICT,
    requirement_level TEXT NOT NULL DEFAULT 'required'
        CHECK (requirement_level IN ('required', 'preferred')),
    PRIMARY KEY (posting_id, skill_id)
) STRICT;

CREATE TABLE contacts (
    contact_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    company_id INTEGER REFERENCES companies(company_id) ON DELETE RESTRICT,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    contact_type TEXT NOT NULL CHECK (contact_type IN
        ('recruiter', 'referrer', 'former_manager', 'alumnus', 'mentor', 'other')),
    email TEXT CHECK (email IS NULL OR
        (email = trim(email) AND email LIKE '%_@_%._%')),
    notes TEXT
) STRICT;

-- UTC timestamps use YYYY-MM-DD HH:MM:SS, so text ordering is chronological.
CREATE TABLE applications (
    application_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    posting_id INTEGER NOT NULL REFERENCES job_postings(posting_id) ON DELETE RESTRICT,
    submitted_at TEXT NOT NULL CHECK (
        length(submitted_at) = 19
        AND strftime('%Y-%m-%d %H:%M:%S', submitted_at, '+0 seconds') IS NOT NULL
        AND strftime('%Y-%m-%d %H:%M:%S', submitted_at, '+0 seconds') = submitted_at),
    last_activity_at TEXT NOT NULL CHECK (
        length(last_activity_at) = 19
        AND strftime('%Y-%m-%d %H:%M:%S', last_activity_at, '+0 seconds') IS NOT NULL
        AND strftime('%Y-%m-%d %H:%M:%S', last_activity_at, '+0 seconds') = last_activity_at),
    notes TEXT,
    UNIQUE (user_id, posting_id),
    CHECK (last_activity_at >= submitted_at)
) STRICT;

CREATE TABLE application_contacts (
    application_id INTEGER NOT NULL REFERENCES applications(application_id) ON DELETE RESTRICT,
    contact_id INTEGER NOT NULL REFERENCES contacts(contact_id) ON DELETE RESTRICT,
    assistance_type TEXT NOT NULL CHECK (assistance_type IN
        ('referral', 'recruiting', 'advice', 'other')),
    notes TEXT,
    PRIMARY KEY (application_id, contact_id)
) STRICT;

CREATE TABLE interviews (
    interview_id INTEGER PRIMARY KEY,
    application_id INTEGER NOT NULL REFERENCES applications(application_id) ON DELETE RESTRICT,
    interview_type TEXT NOT NULL CHECK (interview_type IN
        ('phone_screen', 'technical', 'behavioral', 'final')),
    scheduled_at TEXT NOT NULL CHECK (
        length(scheduled_at) = 19
        AND strftime('%Y-%m-%d %H:%M:%S', scheduled_at, '+0 seconds') IS NOT NULL
        AND strftime('%Y-%m-%d %H:%M:%S', scheduled_at, '+0 seconds') = scheduled_at),
    outcome TEXT CHECK (outcome IN ('passed', 'not_selected', 'cancelled', 'rescheduled')),
    notes TEXT
) STRICT;

CREATE TABLE application_status_history (
    status_event_id INTEGER PRIMARY KEY,
    application_id INTEGER NOT NULL REFERENCES applications(application_id) ON DELETE RESTRICT,
    status TEXT NOT NULL CHECK (status IN
        ('applied', 'interviewing', 'rejected', 'offer', 'accepted', 'withdrawn')),
    changed_at TEXT NOT NULL CHECK (
        length(changed_at) = 19
        AND strftime('%Y-%m-%d %H:%M:%S', changed_at, '+0 seconds') IS NOT NULL
        AND strftime('%Y-%m-%d %H:%M:%S', changed_at, '+0 seconds') = changed_at),
    notes TEXT
) STRICT;

-- Guarantees the ERD's minimum of one status event per application.
CREATE TRIGGER application_initial_status
AFTER INSERT ON applications
BEGIN
    INSERT INTO application_status_history(application_id, status, changed_at, notes)
    VALUES (NEW.application_id, 'applied', NEW.submitted_at, 'Initial submission');
END;

-- Append-only history retains the initial event. Corrections use new events.
CREATE TRIGGER history_no_update BEFORE UPDATE ON application_status_history
BEGIN SELECT RAISE(ABORT, 'Status history is append-only'); END;
CREATE TRIGGER history_no_delete BEFORE DELETE ON application_status_history
BEGIN SELECT RAISE(ABORT, 'Status history is append-only'); END;
CREATE TRIGGER history_valid_time BEFORE INSERT ON application_status_history
WHEN NEW.changed_at < (SELECT submitted_at FROM applications
                      WHERE application_id = NEW.application_id)
BEGIN SELECT RAISE(ABORT, 'Status cannot precede application submission'); END;

-- History depends on a stable application identity and submission time.
CREATE TRIGGER application_identity_fixed
BEFORE UPDATE OF application_id, user_id, posting_id, submitted_at ON applications
WHEN NEW.application_id IS NOT OLD.application_id OR NEW.user_id IS NOT OLD.user_id
  OR NEW.posting_id IS NOT OLD.posting_id OR NEW.submitted_at IS NOT OLD.submitted_at
BEGIN SELECT RAISE(ABORT, 'Application identity and submission time are fixed'); END;
CREATE TRIGGER contact_owner_fixed BEFORE UPDATE OF user_id ON contacts
WHEN NEW.user_id IS NOT OLD.user_id
BEGIN SELECT RAISE(ABORT, 'Contact owner is fixed'); END;

-- A user's application cannot reference another user's private contact.
CREATE TRIGGER application_contact_owner_insert BEFORE INSERT ON application_contacts
WHEN (SELECT user_id FROM applications WHERE application_id = NEW.application_id)
  <> (SELECT user_id FROM contacts WHERE contact_id = NEW.contact_id)
BEGIN SELECT RAISE(ABORT, 'Application and contact must have the same owner'); END;
CREATE TRIGGER application_contact_owner_update BEFORE UPDATE ON application_contacts
WHEN (SELECT user_id FROM applications WHERE application_id = NEW.application_id)
  <> (SELECT user_id FROM contacts WHERE contact_id = NEW.contact_id)
BEGIN SELECT RAISE(ABORT, 'Application and contact must have the same owner'); END;

-- Explicit indexes (separate from indexes SQLite creates for PK/UNIQUE).
CREATE INDEX idx_applications_user_activity ON applications(user_id, last_activity_at);
CREATE INDEX idx_status_application_latest
    ON application_status_history(application_id, changed_at DESC, status_event_id DESC);
CREATE INDEX idx_interviews_application ON interviews(application_id);
CREATE INDEX idx_postings_company ON job_postings(company_id);
CREATE INDEX idx_posting_skills_skill ON posting_skills(skill_id, posting_id);
CREATE INDEX idx_application_contacts_contact ON application_contacts(contact_id);

-- One row per application. Aggregate interviews before joining to avoid
-- multiplying application rows by the number of interviews or status events.
CREATE VIEW application_overview AS
SELECT a.application_id, a.user_id, u.name AS user_name,
       a.posting_id, p.title AS job_title, p.role_type,
       c.company_id, c.company_name, c.industry,
       a.submitted_at, a.last_activity_at,
       h.status AS current_status, h.changed_at AS status_changed_at,
       COALESCE(i.interview_count, 0) AS interview_count
FROM applications AS a
JOIN users AS u ON u.user_id = a.user_id
JOIN job_postings AS p ON p.posting_id = a.posting_id
JOIN companies AS c ON c.company_id = p.company_id
JOIN application_status_history AS h ON h.status_event_id = (
    SELECT sh.status_event_id FROM application_status_history AS sh
    WHERE sh.application_id = a.application_id
    ORDER BY sh.changed_at DESC, sh.status_event_id DESC LIMIT 1
)
LEFT JOIN (
    SELECT application_id, COUNT(*) AS interview_count
    FROM interviews GROUP BY application_id
) AS i ON i.application_id = a.application_id;

COMMIT;
