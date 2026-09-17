UPDATE users
SET
     cv_file_id = $2,
     cv_path = $3,
     updated_at = CURRENT_TIMESTAMP
WHERE id = $1;