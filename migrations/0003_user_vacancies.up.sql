-- User's vacancies table
CREATE TABLE IF NOT EXISTS user_vacancies (
    id SERIAL PRIMARY KEY,

    user_id BIGINT NOT NULL REFERENCES users(id),
    vacancy_id INT NOT NULL REFERENCES vacancies(id),

    match_score INT,
    ai_summary TEXT,
    cover_letter TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (user_id, vacancy_id)
);