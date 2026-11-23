-- NYC Career Launch Tracker | Brett Dowling | Deliverable 4
-- Run after schema.sql and insert_data.sql. All nine queries are read-only.
-- User 1 is Alex Morgan. Fixed dates match the October 22, 2026 sample snapshot.
PRAGMA foreign_keys = ON;

-- Requirement 1: WHERE and ORDER BY
-- Which open jobs advertise a minimum annual salary of at least $80,000?
-- Project operation: filter postings by salary and availability.
SELECT posting_id, title, role_type, location,
       salary_min AS minimum_annual_usd, salary_max AS maximum_annual_usd
FROM job_postings
WHERE posting_status = 'open' AND salary_min >= 80000
ORDER BY salary_min DESC, posting_id;

-- Requirement 2: INNER JOIN
-- Which skills does Alex list, and what is Alex's proficiency in each?
-- Project operation: review the user's skill profile.
SELECT s.skill_name, us.proficiency_level
FROM user_skills AS us
INNER JOIN skills AS s ON s.skill_id = us.skill_id
WHERE us.user_id = 1
ORDER BY s.skill_name;

-- Requirement 3: LEFT JOIN
-- Who are Alex's networking contacts, including those with no known employer?
-- Drew Patel has no company; the LEFT JOIN keeps that contact in the report.
SELECT ct.name AS contact_name, ct.contact_type,
       COALESCE(c.company_name, 'Employer unknown') AS company_name
FROM contacts AS ct
LEFT JOIN companies AS c ON c.company_id = ct.company_id
WHERE ct.user_id = 1
ORDER BY ct.name;

-- Requirement 4: Join involving at least three tables
-- Proposal report: which open postings best match Alex's required skills?
-- Joins postings, companies, posting_skills, and user_skills. Preferred skills
-- are excluded. No required skills recorded means an unknown (NULL) percentage.
SELECT p.posting_id, c.company_name, p.title,
       COUNT(ps.skill_id) AS required_skill_count,
       COUNT(us.skill_id) AS matched_skill_count,
       ROUND(100.0 * COUNT(us.skill_id) / NULLIF(COUNT(ps.skill_id), 0), 1)
           AS required_skill_match_percent
FROM job_postings AS p
INNER JOIN companies AS c ON c.company_id = p.company_id
LEFT JOIN posting_skills AS ps
    ON ps.posting_id = p.posting_id AND ps.requirement_level = 'required'
LEFT JOIN user_skills AS us
    ON us.skill_id = ps.skill_id AND us.user_id = 1
WHERE p.posting_status = 'open'
GROUP BY p.posting_id, c.company_name, p.title
ORDER BY required_skill_match_percent DESC, p.posting_id;

-- Requirement 5: Aggregate query
-- Proposal report: what is the average advertised salary range for open
-- Data Analytics roles? Use only postings with BOTH bounds so the averages
-- describe the same group of postings; report the sample size as well.
SELECT COUNT(*) AS postings_with_complete_salary,
       ROUND(AVG(salary_min), 2) AS average_minimum_annual_usd,
       ROUND(AVG(salary_max), 2) AS average_maximum_annual_usd
FROM job_postings
WHERE posting_status = 'open' AND role_type = 'Data Analytics'
  AND salary_min IS NOT NULL AND salary_max IS NOT NULL;

-- Requirement 6: GROUP BY and HAVING
-- Proposal report: which skills are required by at least two open IT Support
-- postings? HAVING excludes less frequently required skills from the results.
SELECT s.skill_name, COUNT(*) AS postings_requiring_skill
FROM skills AS s
INNER JOIN posting_skills AS ps ON ps.skill_id = s.skill_id
INNER JOIN job_postings AS p ON p.posting_id = ps.posting_id
WHERE p.posting_status = 'open' AND p.role_type = 'IT Support'
  AND ps.requirement_level = 'required'
GROUP BY s.skill_id, s.skill_name
HAVING COUNT(*) >= 2
ORDER BY postings_requiring_skill DESC, s.skill_name;

-- Requirement 7: Subquery
-- Proposal report: which open jobs at companies where Alex has a contact
-- has Alex NOT applied to? EXISTS avoids duplicate jobs when multiple contacts
-- work for one company; NOT EXISTS excludes Alex's existing applications.
SELECT p.posting_id, c.company_name, p.title
FROM job_postings AS p
INNER JOIN companies AS c ON c.company_id = p.company_id
WHERE p.posting_status = 'open'
  AND EXISTS (
      SELECT 1 FROM contacts AS ct
      WHERE ct.user_id = 1 AND ct.company_id = p.company_id
  )
  AND NOT EXISTS (
      SELECT 1 FROM applications AS a
      WHERE a.user_id = 1 AND a.posting_id = p.posting_id
  )
ORDER BY c.company_name, p.title;

-- Requirement 8: Set operation (EXCEPT)
-- Proposal report: which required skills for open Data Science postings is
-- Alex missing? Subtract Alex's skill set from the set of required skills.
-- SQLite EXCEPT returns distinct skills, even if multiple jobs require them.
SELECT s.skill_name AS missing_skill
FROM skills AS s
INNER JOIN posting_skills AS ps ON ps.skill_id = s.skill_id
INNER JOIN job_postings AS p ON p.posting_id = ps.posting_id
WHERE p.posting_status = 'open' AND p.role_type = 'Data Science'
  AND ps.requirement_level = 'required'
EXCEPT
SELECT s.skill_name
FROM skills AS s
INNER JOIN user_skills AS us ON us.skill_id = s.skill_id
WHERE us.user_id = 1
ORDER BY missing_skill;

-- Requirement 9: Query using the Deliverable 3 view
-- Proposal report: which of Alex's active applications have had no update
-- for more than two weeks? The view supplies company, title, latest status,
-- and interview count without repeating its underlying joins.
-- Use the snapshot time so grading later does not change the expected result.
SELECT application_id, company_name, job_title, current_status,
       interview_count, last_activity_at,
       CAST(julianday('2026-10-22 17:00:00') - julianday(last_activity_at) AS INTEGER)
           AS days_since_activity
FROM application_overview
WHERE user_id = 1 AND current_status IN ('applied', 'interviewing')
  AND last_activity_at < datetime('2026-10-22 17:00:00', '-14 days')
ORDER BY last_activity_at, application_id;
