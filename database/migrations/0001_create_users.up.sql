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