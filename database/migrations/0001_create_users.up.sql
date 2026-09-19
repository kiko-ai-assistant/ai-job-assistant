-- Users table
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,  -- Telegram ID
    username VARCHAR(64),
    first_name VARCHAR(64),
    language VARCHAR(5) DEFAULT 'en',
    cv_file_id TEXT, -- Telegram File ID
    cv_path TEXT, -- Path to CV file
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- User search settings table
CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skills jsonb DEFAULT '[]'::jsonb,
    grade VARCHAR(20),  -- Intern/Junior/Senior and etc
    job_type TEXT,  -- Such as remote, contract, etc.
    location TEXT,  -- If specified - country/city
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);