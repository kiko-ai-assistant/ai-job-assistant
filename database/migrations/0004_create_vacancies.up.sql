-- Vacancies table
CREATE TABLE IF NOT EXISTS vacancies (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_id TEXT NOT NULL,  -- ID of vacancy in HH.ru, Telegram channels or other sources
    source TEXT NOT NULL,  -- Such as HH.ru, LinkedIn, Telegram
    title TEXT NOT NULL,
    company TEXT,
    salary_text TEXT,
    location TEXT,
    description TEXT,
    url TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    parsed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_vacancies_source ON vacancies(source);
CREATE INDEX IF NOT EXISTS idx_vacancies_company ON vacancies(company);
CREATE INDEX IF NOT EXISTS idx_vacancies_parsed_at ON vacancies(parsed_at);