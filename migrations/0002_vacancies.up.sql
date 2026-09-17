-- Vacancies table
CREATE TABLE IF NOT EXISTS vacancies (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(100) NOT NULL,  -- ID of vacancy in HH.ru, Telegram channels or other sources
    source VARCHAR(20) NOT NULL,  -- Such as HH.ru, LinkedIn, Telegram

    title TEXT NOT NULL,
    company VARCHAR(255),
    salary_text TEXT,
    location TEXT,

    description TEXT,

    url TEXT NOT NULL,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    parsed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vacancies_source ON vacancies(source);
CREATE INDEX IF NOT EXISTS idx_vacancies_company ON vacancies(company);
CREATE INDEX IF NOT EXISTS idx_vacancies_created ON vacancies(created_at);