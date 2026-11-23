-- NYC Career Launch Tracker | Brett Dowling | Deliverable 4
-- Operation: Alex receives an interview invitation for application 3.
-- Scheduling the interview, recording the new status, and updating activity
-- must succeed together so the calendar, dashboard, and follow-up list agree.
-- Fixed timestamps continue the sample's October 22, 2026 timeline.
PRAGMA foreign_keys = ON;

SELECT 'Before transaction' AS demo_stage,
       application_id, current_status, interview_count, last_activity_at
FROM application_overview WHERE application_id = 3;

BEGIN IMMEDIATE;

INSERT INTO interviews
    (application_id, interview_type, scheduled_at, outcome, notes)
VALUES
    (3, 'phone_screen', '2026-10-29 14:00:00', NULL,
     'Invitation received October 22; first discussion with the hiring team.');

INSERT INTO application_status_history
    (application_id, status, changed_at, notes)
VALUES
    (3, 'interviewing', '2026-10-22 18:00:00',
     'Phone screen scheduled after receiving an interview invitation.');

UPDATE applications
SET last_activity_at = '2026-10-22 18:00:00'
WHERE application_id = 3;

-- The view now shows interviewing, one interview, and the new activity time.
SELECT 'Inside transaction' AS demo_stage,
       application_id, current_status, interview_count, last_activity_at
FROM application_overview WHERE application_id = 3;

-- In normal operation COMMIT would save all three changes.
-- ROLLBACK makes this demonstration repeatable without altering sample data.
ROLLBACK;

-- Expected: applied, zero interviews, and original activity time restored.
SELECT 'After rollback' AS demo_stage,
       application_id, current_status, interview_count, last_activity_at
FROM application_overview WHERE application_id = 3;
