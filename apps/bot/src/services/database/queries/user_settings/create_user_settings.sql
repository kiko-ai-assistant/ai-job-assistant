INSERT INTO user_settings (
    user_id,
    skills,
    grade,
    job_type,
    location
)
VALUES ($1, $2, $3, $4, $5)
RETURNING *;