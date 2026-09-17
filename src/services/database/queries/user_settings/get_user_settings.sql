SELECT
    id,
    user_id,
    skills,
    grade,
    job_type,
    location,
    updated_at
FROM user_settings
WHERE user_id = $1;