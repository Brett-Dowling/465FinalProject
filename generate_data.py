"""Regenerate insert_data.sql using deterministic, fictional sample records.
No third-party packages, random data, network access, or personal information.
Running this script writes SQL only; it never modifies a database.
"""
from pathlib import Path

DATA = {}
DATA['users'] = (['user_id', 'name', 'email'], [
    (1, 'Alex Morgan', 'alex.morgan@example.com'),
    (2, 'Priya Shah', 'priya.shah@example.com'),
    (3, 'Jordan Lee', 'jordan.lee@example.com'),
    (4, 'Sam Rivera', 'sam.rivera@example.com'),
    (5, 'Casey Brooks', 'casey.brooks@example.com'),
])
DATA['companies'] = (['company_id', 'company_name', 'industry', 'hq_borough', 'company_size'], [
    (1, 'Harbor Metrics', 'Analytics', 'Manhattan', '51-200'),
    (2, 'Brooklyn Byteworks', 'Software', 'Brooklyn', '11-50'),
    (3, 'Queens Health Systems', 'Healthcare', 'Queens', '501-1000'),
    (4, 'Hudson Payments', 'Financial Technology', 'Manhattan', '201-500'),
    (5, 'Northstar Cloud Labs', 'Software', None, '51-200'),
    (6, 'Bronx Community Tech', 'Nonprofit', 'Bronx', '11-50'),
])
DATA['skills'] = (['skill_id', 'skill_name'], list(enumerate([
    'Python', 'SQL', 'Java', 'JavaScript', 'Excel', 'Tableau',
    'Machine Learning', 'Git', 'AWS', 'Linux', 'Communication', 'Rust'], 1)))
DATA['job_postings'] = (['posting_id', 'company_id', 'title', 'role_type', 'location',
                        'salary_min', 'salary_max', 'posting_status', 'posting_url', 'posted_date'], [
    (1, 1, 'Junior Data Analyst', 'Data Analytics', 'Manhattan - hybrid', 75000, 90000, 'open', 'https://example.com/jobs/1', '2026-09-01'),
    (2, 1, 'Associate Data Scientist', 'Data Science', 'Manhattan - hybrid', 95000, 115000, 'open', 'https://example.com/jobs/2', '2026-09-03'),
    (3, 2, 'Junior Backend Engineer', 'Software Engineering', 'Brooklyn - onsite', 85000, 105000, 'open', 'https://example.com/jobs/3', '2026-09-02'),
    (4, 2, 'Frontend Developer', 'Software Engineering', 'Brooklyn - hybrid', 80000, 100000, 'closed', 'https://example.com/jobs/4', '2026-09-01'),
    (5, 3, 'Healthcare Data Analyst', 'Data Analytics', 'Queens - onsite', 70000, 85000, 'open', 'https://example.com/jobs/5', '2026-09-04'),
    (6, 3, 'IT Support Associate', 'IT Support', 'Queens - onsite', 55000, 68000, 'open', None, '2026-09-06'),
    (7, 4, 'Graduate Software Engineer', 'Software Engineering', 'Manhattan - hybrid', 100000, 125000, 'closed', 'https://example.com/jobs/7', '2026-09-01'),
    (8, 4, 'Product Analyst', 'Product', 'Manhattan - hybrid', 85000, 105000, 'paused', 'https://example.com/jobs/8', '2026-09-08'),
    (9, 5, 'Cloud Support Engineer', 'IT Support', 'Remote - NYC eligible', 70000, 90000, 'open', 'https://example.com/jobs/9', '2026-09-10'),
    (10, 5, 'Junior Platform Engineer', 'Software Engineering', 'Remote - NYC eligible', 95000, None, 'open', 'https://example.com/jobs/10', '2026-09-15'),
    (11, 1, 'Reporting Assistant', 'Data Analytics', 'Manhattan - onsite', None, None, 'open', None, None),
    (12, 2, 'Developer Support Associate', 'IT Support', 'Brooklyn - hybrid', 60000, 75000, 'open', 'https://example.com/jobs/12', '2026-10-01'),
])
DATA['user_skills'] = (['user_id', 'skill_id', 'proficiency_level'], [
    (1,1,'advanced'),(1,2,'intermediate'),(1,8,'intermediate'),(1,4,'beginner'),
    (2,1,'intermediate'),(2,2,'advanced'),(2,5,'advanced'),(2,6,'intermediate'),(2,7,'beginner'),
    (3,3,'advanced'),(3,8,'intermediate'),(3,4,'intermediate'),(3,2,'beginner'),
    (4,9,'beginner'),(4,10,'intermediate'),(4,11,'advanced'),(4,1,'beginner'),
])
requirements = {
    1: ([2,5], [1,6]), 2: ([1,2,7], [9]), 3: ([1,8], [2]),
    4: ([4,8], [11]), 5: ([2,5], [6]), 6: ([10,11], [9]),
    7: ([3,8], [2]), 8: ([2,11], [5]), 9: ([9,10], [1]),
    10: ([1,9,10], [8]), 12: ([], [11]),
}
DATA['posting_skills'] = (['posting_id', 'skill_id', 'requirement_level'], [
    (posting, skill, level) for posting, (required, preferred) in requirements.items()
    for level, skills in [('required', required), ('preferred', preferred)] for skill in skills
])
DATA['contacts'] = (['contact_id', 'user_id', 'company_id', 'name', 'contact_type', 'email', 'notes'], [
    (1,1,1,'Taylor Quinn','recruiter','taylor.quinn@example.com','Met at a campus career fair.'),
    (2,1,1,'Riley Chen','alumnus','riley.chen@example.com','Shared advice about analyst interviews.'),
    (3,1,None,'Drew Patel','mentor',None,'Current employer not recorded.'),
    (4,2,1,'Jamie Park','referrer','jamie.park@example.com','Offered to refer a suitable role.'),
    (5,2,3,'Morgan Ellis','recruiter','morgan.ellis@example.com','Healthcare analytics recruiting contact.'),
    (6,3,2,'Avery Lane','former_manager','avery.lane@example.com','Former internship manager.'),
    (7,3,4,'Robin Diaz','recruiter','robin.diaz@example.com','Graduate engineering recruitment.'),
    (8,4,5,'Cameron Reed','alumnus','cameron.reed@example.com','Works on the cloud support team.'),
    (9,4,6,'Dakota Wells','mentor',None,'Networking connection; no matching posting yet.'),
])
# Fixed snapshot as of 2026-10-22. Activity dates represent logged changes,
# not scheduled future interviews. A user may apply to multiple postings;
# multiple users may apply to the same posting.
applications = [
    (1,1,1,'09-10','10-20'), (2,1,3,'09-12','10-06'),
    (3,1,2,'09-15','09-15'), (4,1,10,'10-05','10-21'),
    (5,2,1,'09-11','10-08'), (6,2,2,'09-16','10-21'),
    (7,2,5,'09-20','10-15'), (8,2,8,'09-22','10-07'),
    (9,3,3,'09-13','10-16'), (10,3,4,'09-14','09-30'),
    (11,3,7,'09-18','10-19'), (12,3,10,'10-06','10-06'),
    (13,4,6,'09-21','10-20'), (14,4,9,'09-23','10-20'),
    (15,4,12,'10-03','10-03'), (16,1,9,'10-07','10-07'),
]
DATA['applications'] = (['application_id','user_id','posting_id','submitted_at','last_activity_at','notes'], [
    (aid,uid,pid,f'2026-{submitted} 09:00:00',f'2026-{activity} 17:00:00',
     'Submitted through the employer careers page.')
    for aid,uid,pid,submitted,activity in applications
])
DATA['application_contacts'] = (['application_id','contact_id','assistance_type','notes'], [
    (1,1,'recruiting','Arranged the first conversation.'),
    (1,2,'referral','Submitted an employee referral.'),
    (2,3,'advice','Reviewed the resume before submission.'),
    (3,1,'recruiting','Confirmed the posting is still open.'),
    (4,3,'advice','Practiced technical interview questions.'),
    (5,4,'referral','Referred the analyst application.'),
    (6,4,'advice','Discussed the data science interview format.'),
    (7,5,'recruiting','Explained the hiring timeline.'),
    (9,6,'referral','Provided a reference from the internship.'),
    (10,6,'advice','Reviewed the portfolio.'),
    (11,7,'recruiting','Coordinated interview rounds.'),
    (14,8,'referral','Submitted a cloud support referral.'),
])
DATA['interviews'] = (['interview_id','application_id','interview_type','scheduled_at','outcome','notes'], [
    (1,1,'phone_screen','2026-10-01 14:00:00','passed','Discussed analyst responsibilities.'),
    (2,1,'technical','2026-10-15 15:00:00','passed','Completed SQL exercises.'),
    (3,1,'final','2026-10-26 16:00:00',None,'Scheduled on October 20; outcome pending.'),
    (4,2,'phone_screen','2026-09-25 13:00:00','not_selected','Role needed more production experience.'),
    (5,5,'phone_screen','2026-09-24 14:00:00','passed','Moved to technical round.'),
    (6,5,'technical','2026-10-05 15:00:00','not_selected','Received rejection on October 8.'),
    (7,6,'phone_screen','2026-10-09 14:00:00','passed','Discussed a capstone project.'),
    (8,6,'technical','2026-10-28 15:00:00',None,'Scheduled on October 21.'),
    (9,9,'phone_screen','2026-09-28 13:00:00','passed','Backend experience aligned with the role.'),
    (10,9,'technical','2026-10-08 14:00:00','passed','Completed the coding exercise.'),
    (11,9,'final','2026-10-14 16:00:00','passed','Offer received on October 16.'),
    (12,11,'phone_screen','2026-09-29 14:00:00','passed','Graduate program screening.'),
    (13,11,'technical','2026-10-09 15:00:00','passed','Java and data structures assessment.'),
    (14,13,'phone_screen','2026-10-19 14:00:00','rescheduled','New time arranged on October 20.'),
    (15,13,'phone_screen','2026-10-27 14:00:00',None,'Rescheduled session.'),
    (16,14,'phone_screen','2026-10-13 14:00:00','passed','Discussed Linux troubleshooting.'),
    (17,14,'technical','2026-10-20 15:00:00','passed','Awaiting a hiring decision.'),
])
events = [
    (1,'interviewing','09-28'), (2,'interviewing','09-23'),(2,'rejected','10-06'),
    (4,'interviewing','10-21'), (5,'interviewing','09-22'),(5,'rejected','10-08'),
    (6,'interviewing','10-07'), (7,'rejected','10-15'),(8,'withdrawn','10-07'),
    (9,'interviewing','09-25'),(9,'offer','10-16'),(10,'rejected','09-30'),
    (11,'interviewing','09-27'),(11,'offer','10-16'),(11,'accepted','10-19'),
    (13,'interviewing','10-15'),(14,'interviewing','10-09'),
]
# Application INSERT triggers already created the 16 initial applied events.
DATA['application_status_history'] = (['status_event_id','application_id','status','changed_at','notes'], [
    (100+i,aid,status,f'2026-{day} 12:00:00',f'Logged status: {status}.')
    for i,(aid,status,day) in enumerate(events,1)
])

def literal(value):
    if value is None:
        return 'NULL'
    if isinstance(value, int):
        return str(value)
    return "'" + value.replace("'", "''") + "'"

def main():
    parts = ['-- Deterministic synthetic data; generated by generate_data.py.',
             '-- Snapshot: 2026-10-22. All names, companies, and activity are fictional.',
             '-- Run schema.sql first. Do not run this twice without rebuilding.',
             'PRAGMA foreign_keys = ON;', 'BEGIN IMMEDIATE;', '']
    for table, (columns, rows) in DATA.items():
        parts.append(f'-- {table}: {len(rows)} explicit rows')
        parts.append(f'INSERT INTO {table} ({", ".join(columns)}) VALUES')
        parts.append(',\n'.join('    (' + ', '.join(map(literal,row)) + ')' for row in rows) + ';\n')
    parts.append('COMMIT;\n')
    target=Path(__file__).resolve().with_name('insert_data.sql')
    target.write_text('\n'.join(parts),encoding='utf-8')
    counts={table:len(rows) for table,(_,rows) in DATA.items()}
    counts['application_status_history'] += len(applications)
    print('Wrote', target.name)
    for table,count in counts.items():print(f'  {table}: {count}')
    print('Total stored rows:',sum(counts.values()))

if __name__=='__main__':
    main()
