UPDATE user_settings
SET
    skills = $2,
    grade = $3,
    job_type = $4,
    location = $5,
    updated_at = CURRENT_TIMESTAMP
WHERE user_id = $1;