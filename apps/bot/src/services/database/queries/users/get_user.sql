SELECT
    id,
    username,
    first_name,
    language,
    cv_file_id,
    cv_path,
    created_at,
    updated_at
FROM users
WHERE id = $1;