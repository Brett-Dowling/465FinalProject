"""Run with: python app.py"""
import argparse
from pathlib import Path
import sqlite3
import textwrap

import database as db


class Cancelled(Exception):
    pass


def prompt(label):
    value = input(label).strip()
    if value.lower() == 'cancel':
        raise Cancelled
    return value


def number(label, optional=False, minimum=1, maximum=2147483647):
    while True:
        value = prompt(label)
        if optional and not value:
            return None
        try:
            result = int(value)
            if minimum <= result <= maximum:
                return result
        except ValueError:
            pass
        print(f'Enter a whole number from {minimum} to {maximum}.')


def choose(label, values):
    for index, value in enumerate(values, 1):
        print(f'  {index}. {value.replace("_", " ")}')
    return values[number(label, maximum=len(values)) - 1]


def show_records(rows):
    """Readable narrow-terminal output without clipping long notes or titles."""
    if not rows:
        print('No matching records.')
        return
    for row in rows:
        print('-' * 64)
        for key in row.keys():
            value = 'Not recorded' if row[key] is None else str(row[key])
            label = key.replace('_', ' ').capitalize()
            print(textwrap.fill(f'{label}: {value}', width=78, subsequent_indent='  '))
    print(f'({len(rows)} record(s))')


def select_user(con):
    show_records(db.list_users(con))
    user_id = number('Select user ID (0 to exit): ', minimum=0)
    if user_id == 0:
        return None
    user = con.execute('SELECT user_id, name FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if user is None:
        raise db.InputError('User ID not found. Choose one of the listed users.')
    return user


def browse(con, user_id):
    keyword = prompt('Job title or company keyword (Enter for all): ')
    salary = number('Minimum advertised annual salary in USD (Enter for any): ',
                    optional=True, minimum=0)
    print('\nOpen jobs; unknown salary bounds display as Not recorded.')
    show_records(db.browse_jobs(con, keyword, salary))


def applications(con, user_id):
    rows = db.my_applications(con, user_id)
    show_records(rows)
    if not rows:
        return
    app_id = number('Application ID for details (Enter to return): ', optional=True)
    if app_id is None:
        return
    app, interviews, contacts, history = db.application_details(con, user_id, app_id)
    print('\nApplication notes:', app['notes'] or 'None')
    print('\nInterviews (UTC)')
    show_records(interviews)
    print('\nContacts assisting with this application')
    show_records(contacts)
    print('\nStatus history')
    show_records(history)


def apply(con, user_id):
    show_records(db.browse_jobs(con))
    posting_id = number('Posting ID to apply for: ')
    notes = prompt('Application notes (optional): ')
    app_id = db.add_application(con, user_id, posting_id, notes)
    print(f'Application {app_id} saved with status applied.')


def edit(con, user_id):
    show_records(db.my_applications(con, user_id))
    app_id = number('Application ID to edit: ')
    app = db.require_application(con, user_id, app_id)
    print('Current notes:', app['notes'] or 'None')
    notes = prompt('Replacement notes (Enter to clear): ')
    db.edit_notes(con, user_id, app_id, notes)
    print('Notes and activity timestamp updated.')


def report(con, user_id):
    days = number('Follow up after how many inactive days? (Enter for 14): ',
                  optional=True, maximum=365)
    summary, overdue = db.reports(con, user_id, 14 if days is None else days)
    print('\nApplication status summary')
    show_records(summary)
    print('\nActive applications needing follow-up (based on current UTC time)')
    show_records(overdue)


def interview(con, user_id):
    show_records(db.my_applications(con, user_id))
    app_id = number('Application ID for the interview: ')
    db.require_application(con, user_id, app_id)
    kind = choose('Interview type number: ', db.INTERVIEW_TYPES)
    scheduled_at = prompt('Future interview date/time in UTC (YYYY-MM-DD HH:MM): ')
    notes = prompt('Interview notes (optional): ')
    db.schedule_interview(con, user_id, app_id, kind, scheduled_at, notes)
    print('Interview saved. Application status and activity are up to date.')


def status(con, user_id):
    show_records(db.my_applications(con, user_id))
    app_id = number('Application ID to update: ')
    app = db.require_application(con, user_id, app_id)
    print('Current status:', app['current_status'])
    new_status = choose('New status number: ', db.STATUSES)
    notes = prompt('Status update notes (optional): ')
    db.change_status(con, user_id, app_id, new_status, notes)
    print('Status history and activity timestamp updated.')


def error_message(exc):
    if isinstance(exc, db.InputError):
        return str(exc)
    if isinstance(exc, sqlite3.IntegrityError):
        return 'That change conflicts with a database rule. Check the ID, duplicate records, or values.'
    if isinstance(exc, sqlite3.OperationalError) and 'locked' in str(exc).lower():
        return 'The database is busy in another program. Close that program or try again.'
    return 'The database operation could not finish. Check the database file and folder permissions.'


def run(con):
    actions = {'1': browse, '2': applications, '3': apply, '4': edit,
               '5': report, '6': interview, '7': status}
    user = None
    while True:
        try:
            if user is None:
                user = select_user(con)
                if user is None:
                    return
            print(f'\nNYC Career Launch Tracker | {user["name"]}')
            print('1. Browse or search open jobs')
            print('2. View my applications and related details')
            print('3. Apply for a job')
            print('4. Edit application notes')
            print('5. View status summary and follow-up report')
            print('6. Schedule an interview')
            print('7. Update application status')
            print('8. Switch user profile')
            print('0. Exit')
            choice = prompt('Choose an option: ')
            if choice == '0':
                return
            if choice == '8':
                user = None
            elif choice in actions:
                actions[choice](con, user['user_id'])
            else:
                print('Choose a menu number from 0 to 8.')
        except Cancelled:
            print('Cancelled. No pending changes saved.')
        except (db.InputError, sqlite3.Error) as exc:
            con.rollback()
            print(error_message(exc))


def main():
    parser = argparse.ArgumentParser(description='Interactive NYC Career Launch Tracker')
    parser.add_argument('--db', type=Path,
                        default=Path(__file__).resolve().with_name('career_tracker_app.db'),
                        help='SQLite file path; defaults to the application folder')
    args = parser.parse_args()
    con = None
    try:
        con, fresh = db.connect_database(args.db)
        print('Sample database created.' if fresh else 'Existing database opened; saved changes preserved.')
        print('Type cancel at a prompt to return without saving. All dates/times are UTC.')
        print('Select a demo user profile. This local class project does not provide login security.')
        run(con)
    except (EOFError, KeyboardInterrupt):
        print('\nExiting; unfinished changes will not be saved.')
    except (OSError, sqlite3.Error, db.InputError) as exc:
        if isinstance(exc, db.InputError):
            print(str(exc))
        else:
            print('Could not open or initialize the database. Keep the submitted files together,')
            print('use a writable folder, and choose a project database file with --db.')
        return 1
    finally:
        if con is not None:
            con.rollback()
            con.close()
    print('Goodbye. Saved changes will be available next time.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
