-- User's vacancies table
CREATE TABLE IF NOT EXISTS user_vacancies (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    vacancy_id BIGINT NOT NULL REFERENCES vacancies(id) ON DELETE CASCADE,

    match_score INT CHECK (match_score BETWEEN 0 AND 100),
    ai_summary TEXT,
    cover_letter TEXT,

    is_seen BOOLEAN, 
    is_favorite BOOLEAN,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (user_id, vacancy_id)
);

CREATE INDEX IF NOT EXISTS idx_match_score ON user_vacancies(match_score);