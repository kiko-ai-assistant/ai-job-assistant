-- name: CreateVacancy :exec
INSERT INTO vacancies (
    id,
    external_id,
    source,
    title,
    company,
    salary_text,
    salary_from,
    salary_to,
    currency,
    grade,
    employment_types,
    location_text,
    country,
    city,
    description,
    url,
    published_at,
    parsed_at
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
    $11, $12, $13, $14, $15, $16, $17, $18
);

-- name: CreateManyVacancies :batchone
INSERT INTO vacancies (
    id,
    external_id,
    source,
    title,
    company,
    salary_text,
    salary_from,
    salary_to,
    currency,
    grade,
    employment_types,
    location_text,
    country,
    city,
    description,
    url,
    published_at,
    parsed_at
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
    $11, $12, $13, $14, $15, $16, $17, $18
)
ON CONFLICT (source, external_id) DO NOTHING
RETURNING id;

-- name: GetVacancy :one
SELECT
    id,
    external_id,
    source,
    title,
    company,
    salary_text,
    salary_from,
    salary_to,
    currency,
    grade,
    employment_types,
    location_text,
    country,
    city,
    description,
    url,
    published_at,
    parsed_at
FROM vacancies
WHERE id = $1;

-- name: ListVacancies :many
SELECT
    id,
    external_id,
    source,
    title,
    company,
    salary_text,
    salary_from,
    salary_to,
    currency,
    grade,
    employment_types,
    location_text,
    country,
    city,
    description,
    url,
    published_at,
    parsed_at
FROM vacancies
ORDER BY published_at DESC;