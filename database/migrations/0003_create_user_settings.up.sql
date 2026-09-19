CREATE TYPE grade AS ENUM ('INTERN', 'JUNIOR', 'MIDDLE', 'SENIOR', 'LEAD');

CREATE TYPE employment_type AS ENUM ('REMOTE', 'OFFICE', 'HYBRID', 'CONTRACT');

-- User search settings table
CREATE TABLE IF NOT EXISTS user_settings (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skills jsonb DEFAULT '[]'::jsonb,
    grade grade,  -- Intern/Junior/Senior and etc
    employment_type employment_type,  -- Such as remote, contract, etc.
    location TEXT,  -- If specified - country/city
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username) WHERE username IS NOT NULL;