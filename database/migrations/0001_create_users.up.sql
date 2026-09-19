-- language_interface enum ('EN', 'RU', 'CN')
CREATE TYPE interface_lang AS ENUM ('EN', 'RU', 'CN');

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- USER ID
    telegram_id BIGINT UNIQUE NOT NULL, -- TELEGRAM ID (52-bit unique number)
    username TEXT, -- TG USERNAME
    first_name TEXT NOT NULL, -- TG FSTNAME
    last_name TEXT,
    language interface_lang DEFAULT 'EN', -- INTERFACE LANGUAGE
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS curriculum_vitae (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cv_file_id TEXT NOT NULL,
    cv_path TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

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