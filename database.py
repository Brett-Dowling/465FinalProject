"""SQLite operations for the NYC Career Launch Tracker."""
from datetime import datetime, timezone
from pathlib import Path
import sqlite3


class InputError(Exception):
    """A user-facing validation message."""


def now_utc():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def connect_database(path):
    """Initialize a new database from submitted SQL; preserve an existing one."""
    if sqlite3.sqlite_version_info < (3, 37, 0):
        raise InputError('SQLite 3.37 or newer is required. Please install a newer Python version.')
    path = Path(path)
    fresh = not path.exists()
    con = None
    try:
        if fresh:
            base = Path(__file__).resolve().parent
            schema = (base / 'schema.sql').read_text(encoding='utf-8')
            sample = (base / 'insert_data.sql').read_text(encoding='utf-8')
            # Build in memory first so an invalid setup cannot leave a partial file.
            seed = sqlite3.connect(':memory:')
            try:
                seed.executescript(schema)
                seed.executescript(sample)
                con = sqlite3.connect(path)
                seed.backup(con)
            finally:
                seed.close()
        else:
            con = sqlite3.connect(path)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys = ON')
        if con.execute('PRAGMA foreign_keys').fetchone()[0] != 1:
            raise InputError('Foreign-key enforcement could not be enabled.')
        con.execute('SELECT application_id FROM application_overview LIMIT 1')
        return con, fresh
    except Exception:
        if con is not None:
            con.close()
        raise


def list_users(con):
    return con.execute('SELECT user_id, name FROM users ORDER BY name').fetchall()


def browse_jobs(con, keyword='', minimum_salary=None):
    if minimum_salary is not None and minimum_salary < 0:
        raise InputError('Minimum salary cannot be negative.')
    # instr treats %, _, and quotes literally; values are still parameterized.
    return con.execute('''
        SELECT p.posting_id, c.company_name, p.title, p.role_type,
               p.location, p.salary_min, p.salary_max
        FROM job_postings p JOIN companies c ON c.company_id = p.company_id
        WHERE p.posting_status = 'open'
          AND (instr(lower(p.title), lower(?)) > 0
               OR instr(lower(c.company_name), lower(?)) > 0)
          AND (? IS NULL OR p.salary_min >= ?)
        ORDER BY p.salary_min DESC, p.posting_id
    ''', (keyword, keyword, minimum_salary, minimum_salary)).fetchall()


def my_applications(con, user_id):
    return con.execute('''
        SELECT application_id, company_name, job_title, current_status,
               interview_count, last_activity_at
        FROM application_overview WHERE user_id = ?
        ORDER BY last_activity_at DESC, application_id
    ''', (user_id,)).fetchall()


def require_application(con, user_id, application_id):
    row = con.execute('''
        SELECT a.*, v.current_status FROM applications a
        JOIN application_overview v ON v.application_id = a.application_id
        WHERE a.application_id = ? AND a.user_id = ?
    ''', (application_id, user_id)).fetchone()
    if row is None:
        raise InputError('Application not found in the selected user profile.')
    return row


def application_details(con, user_id, application_id):
    application = require_application(con, user_id, application_id)
    interviews = con.execute('''
        SELECT interview_type, scheduled_at, outcome, notes FROM interviews
        WHERE application_id = ? ORDER BY scheduled_at, interview_id
    ''', (application_id,)).fetchall()
    contacts = con.execute('''
        SELECT c.name, ac.assistance_type, ac.notes
        FROM application_contacts ac JOIN contacts c ON c.contact_id = ac.contact_id
        WHERE ac.application_id = ? ORDER BY c.name
    ''', (application_id,)).fetchall()
    history = con.execute('''
        SELECT status, changed_at, notes FROM application_status_history
        WHERE application_id = ? ORDER BY changed_at, status_event_id
    ''', (application_id,)).fetchall()
    return application, interviews, contacts, history


def add_application(con, user_id, posting_id, notes):
    stamp = now_utc()
    with con:
        con.execute('BEGIN IMMEDIATE')
        posting = con.execute('SELECT posting_status FROM job_postings WHERE posting_id = ?',
                              (posting_id,)).fetchone()
        if posting is None:
            raise InputError('Job posting not found.')
        if posting['posting_status'] != 'open':
            raise InputError('This posting is not open for applications.')
        if con.execute('SELECT 1 FROM applications WHERE user_id = ? AND posting_id = ?',
                       (user_id, posting_id)).fetchone():
            raise InputError('You already have an application for this posting.')
        cur = con.execute('''
            INSERT INTO applications(user_id, posting_id, submitted_at, last_activity_at, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, posting_id, stamp, stamp, notes or None))
        # The schema trigger creates the initial applied status in this transaction.
        return cur.lastrowid


def edit_notes(con, user_id, application_id, notes):
    with con:
        con.execute('BEGIN IMMEDIATE')
        require_application(con, user_id, application_id)
        con.execute('''UPDATE applications SET notes = ?, last_activity_at = ?
                       WHERE application_id = ? AND user_id = ?''',
                    (notes or None, now_utc(), application_id, user_id))


def reports(con, user_id, days):
    if not 1 <= days <= 365:
        raise InputError('Follow-up days must be between 1 and 365.')
    summary = con.execute('''
        SELECT current_status, COUNT(*) AS applications,
               SUM(interview_count) AS interviews
        FROM application_overview WHERE user_id = ?
        GROUP BY current_status ORDER BY applications DESC, current_status
    ''', (user_id,)).fetchall()
    overdue = con.execute('''
        SELECT application_id, company_name, job_title, current_status,
               last_activity_at,
               CAST(julianday(?) - julianday(last_activity_at) AS INTEGER) AS days_idle
        FROM application_overview
        WHERE user_id = ? AND current_status IN ('applied', 'interviewing')
          AND julianday(last_activity_at) < julianday(?) - ?
        ORDER BY last_activity_at, application_id
    ''', (now_utc(), user_id, now_utc(), days)).fetchall()
    return summary, overdue


INTERVIEW_TYPES = ('phone_screen', 'technical', 'behavioral', 'final')
STATUSES = ('interviewing', 'rejected', 'offer', 'accepted', 'withdrawn')


def schedule_interview(con, user_id, application_id, kind, scheduled_at, notes):
    if kind not in INTERVIEW_TYPES:
        raise InputError('Choose one of the listed interview types.')
    try:
        scheduled = datetime.strptime(scheduled_at, '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)
    except ValueError:
        raise InputError('Use a real date and time in YYYY-MM-DD HH:MM format.') from None
    if scheduled.strftime('%Y-%m-%d %H:%M') != scheduled_at:
        raise InputError('Use YYYY-MM-DD HH:MM with two-digit months, days, hours, and minutes.')
    if scheduled <= datetime.now(timezone.utc):
        raise InputError('The interview must be scheduled for a future time (UTC).')
    stamp = now_utc()
    with con:
        con.execute('BEGIN IMMEDIATE')
        app = require_application(con, user_id, application_id)
        if app['current_status'] not in ('applied', 'interviewing'):
            raise InputError('Only applied or interviewing applications can receive a new interview.')
        con.execute('''INSERT INTO interviews
            (application_id, interview_type, scheduled_at, outcome, notes)
            VALUES (?, ?, ?, NULL, ?)''',
            (application_id, kind, scheduled.strftime('%Y-%m-%d %H:%M:%S'), notes or None))
        if app['current_status'] == 'applied':
            con.execute('''INSERT INTO application_status_history
                (application_id, status, changed_at, notes) VALUES (?, 'interviewing', ?, ?)''',
                (application_id, stamp, 'Interview scheduled through the application.'))
        con.execute('UPDATE applications SET last_activity_at = ? WHERE application_id = ?',
                    (stamp, application_id))


def change_status(con, user_id, application_id, status, notes):
    if status not in STATUSES:
        raise InputError('Choose one of the listed statuses.')
    stamp = now_utc()
    with con:
        con.execute('BEGIN IMMEDIATE')
        app = require_application(con, user_id, application_id)
        if app['current_status'] == status:
            raise InputError('That is already the current status.')
        con.execute('''INSERT INTO application_status_history
            (application_id, status, changed_at, notes) VALUES (?, ?, ?, ?)''',
            (application_id, status, stamp, notes or None))
        con.execute('UPDATE applications SET last_activity_at = ? WHERE application_id = ?',
                    (stamp, application_id))
