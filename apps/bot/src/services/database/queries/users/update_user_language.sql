UPDATE users
SET
     language = $2,
     updated_at = CURRENT_TIMESTAMP
WHERE id = $1;