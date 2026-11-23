# NYC Career Launch Tracker

**Brett Dowling — Final Database Project**

## Project overview

NYC Career Launch Tracker helps students and recent graduates organize a job search in the New York City area. It stores companies, job postings, skills, applications, interviews, and networking contacts in a relational database.

The interactive Python application lets users search jobs, track applications, record interviews, and identify applications that need follow-up. The SQL reports also demonstrate skill matching, salary summaries, and networking opportunities.

## Repository files

Keep these files together in the repository's main folder:

| File | Purpose |
|---|---|
| `erd.pdf` | Final ER diagram showing the 11 tables and their relationships |
| `schema.sql` | Tables, constraints, triggers, indexes, and view |
| `insert_data.sql` | Fictional sample data |
| `queries.sql` | Nine labeled SQL queries |
| `transaction.sql` | Multi-step interview transaction with rollback |
| `app.py` | Application menu, prompts, and displayed results |
| `database.py` | Database connections, parameterized SQL, and transactions |
| `run_queries.sh` | Recreates a demonstration database and runs the SQL examples |
| `generate_data.py` | Source script for regenerating the sample INSERT statements |
| `README.md` | Complete project setup and run instructions |

## Requirements

- **Python 3.10 or newer**, with its built-in `sqlite3` library linked to **SQLite 3.37 or newer**.
- **Bash and the SQLite command-line program (`sqlite3`) version 3.37 or newer** to run `run_queries.sh`.
- A writable project folder.

No third-party Python packages, database server, hosted account, passwords, or API keys are required. There is no `pip install` step.

On Windows, the SQL script can run in Git Bash or WSL. The `sqlite3` command must be installed and available on that environment's `PATH`; Python's built-in SQLite library does not supply this command-line program.

Check the required versions:

```bash
python --version
python -c "import sqlite3; print(sqlite3.sqlite_version)"
bash --version
sqlite3 --version
```

On Windows, use `py` instead of `python` if needed. On macOS or Linux, use `python3` if that is the installed command name. Bash and the SQLite command-line program are only needed for the SQL demonstration, not for starting the Python application.

## Start the application

1. Clone or download the repository. Extract it if downloaded as a ZIP.
2. Open a terminal in the folder containing `app.py`.
3. Run:

```bash
python app.py
```

On first launch, the application creates `career_tracker_app.db` beside `app.py`. It automatically runs **`schema.sql` first, then `insert_data.sql`**. No manual SQL editing is necessary.

Later launches reopen that database and preserve saved changes. Choose a user ID from the displayed profiles. User **1, Alex Morgan**, has existing applications; user **5, Casey Brooks**, starts with none.

To create a separate fresh database or open another database with this project's schema:

```bash
python app.py --db practice.db
```

Use a new filename for a fresh sample without overwriting previous work. Relative paths supplied through `--db` are relative to the terminal's current folder. No other connection configuration is required.

## Application operations

| Menu option | Operation |
|---|---|
| **1** | Browse open jobs by title/company keyword and optional minimum salary |
| **2** | View applications with company, job, status, and interview counts; inspect interviews, contacts, and status history |
| **3** | Apply for an open posting and record optional notes |
| **4** | Replace or clear an application's notes |
| **5** | View application totals by status and a follow-up report with a chosen inactivity threshold |
| **6** | Schedule an interview for an applied/interviewing application |
| **7** | Record a new application status |
| **8** | Switch user profiles |
| **0** | Exit and close the database connection |

Type `cancel` at a prompt to cancel the current operation. Changes are saved when a success message appears. Interview dates must be in the future and entered in **UTC**, using `YYYY-MM-DD HH:MM`.

## Recreate the database and run the SQL examples

From the project folder in a Bash-capable terminal, run:

```bash
bash run_queries.sh
```

The script performs these steps in order:

1. Removes the existing `career_tracker_d4.db`, if present.
2. Runs `schema.sql` to create the database structure.
3. Runs `insert_data.sql` to load the sample data.
4. Runs `queries.sql` and displays all nine query results.
5. Runs `transaction.sql`, showing the application before the changes, inside the transaction, and after rollback.
6. Prints a completion message.

**Rerunning this script discards changes in `career_tracker_d4.db`.** It does not reset the default application database, `career_tracker_app.db`.

The two databases use identical schema and sample files. To inspect the SQL demonstration database through the application, run:

```bash
python app.py --db career_tracker_d4.db
```

The SQL files and application enable `PRAGMA foreign_keys = ON`. SQLite requires this setting on each new connection; any additional database client must enable it before starting a transaction.

## Database design and SQL features

The final design contains **11 tables** and matches `erd.pdf`. Junction tables connect users to skills, postings to skills, and applications to assisting contacts. Their composite primary keys prevent duplicate pairs. Applications also enforce one application per user per posting.

Constraints enforce required values, unique emails and skill names, valid status values, and valid salary ranges. Unknown values use `NULL`. Salaries are annual USD amounts, and timestamps use UTC.

The **`application_overview` view** joins applications, users, postings, companies, latest status events, and interview counts. It provides one row per application for dashboards and reports. Explicit indexes support activity-date searches, latest-status retrieval, and common relationship lookups.

`queries.sql` demonstrates filtering and sorting, INNER JOIN, LEFT JOIN, a multi-table join, aggregation, GROUP BY/HAVING, subqueries, EXCEPT, and use of the view. Reports include skill matching, salary averages, missing skills, networking opportunities, and overdue applications.

`transaction.sql` schedules an interview, adds an interviewing status, and updates application activity together. It uses **ROLLBACK** to restore the sample after the demonstration. The Python application commits successful operations and rolls back failed ones.

All user-supplied SQL values use placeholders. The application validates input, checks ownership within the selected profile, and displays friendly errors for invalid operations. SQLite remains the primary data store.

## Sample data

The database starts with **173 fictional records**. Names, companies, and activity are synthetic; email addresses use `example.com`. The sample represents October 2026.

The SQL follow-up example uses a fixed snapshot date for reproducible results. Application reports use current UTC time, so the number of overdue sample applications changes over time.

`insert_data.sql` is already supplied. Running the generator is optional:

```bash
python generate_data.py
```

This regenerates `insert_data.sql`; it does not modify an existing database. Do not reload the INSERT file into a populated database without recreating the schema first.

## Demonstration and verification

For a fresh walkthrough, start with a new database filename and select user 1:

1. Use option **1** to search for `Data` jobs.
2. Use option **2** to inspect application **1**, including its interviews and contacts.
3. Use option **3** to apply for posting **11**. Note the new application ID.
4. Use option **4** to edit that application's notes.
5. Use option **6** to schedule its interview for a future UTC date.
6. Use option **2** to confirm the interview and updated status.
7. Use option **7** to change its status to `offer`, then option **5** to inspect the summary.
8. Try applying for posting 11 again to confirm duplicate handling.
9. Exit and restart with the same database filename. Confirm the notes, interview, and status were saved.

Testing covered all seven operations, invalid input, duplicate applications, ownership checks, persistence after restart, and rollback after a simulated failure. The application passed 58 development checks. The SQL queries and transaction were tested, and the complete Bash workflow was successfully run locally. Development test scripts are not required to run this repository.

## Limitations and known issues

- This is a local class project. Profile selection is not authentication, and users can switch profiles.
- Job postings are sample records; there is no live job-board integration.
- Company, contact, and skill-profile maintenance are not exposed in the current application menu.
- Skill matching is available in the SQL reports, not as a separate application menu option.
- Only one application per user per posting is allowed.
- Direct edits outside the application must maintain `last_activity_at` when logging relevant activity. The application handles this for its own write operations.
- Date-sensitive operations depend on the machine's clock being correct.

There are no known unresolved functional errors from testing. The final schema and ER diagram have no significant structural changes from the earlier database design.
# 465FinalProject
