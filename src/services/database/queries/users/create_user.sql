INSERT INTO users (
    id,
    username,
    first_name,
    language
)
VALUES ($1, $2, $3, $4)
RETURNING *;
