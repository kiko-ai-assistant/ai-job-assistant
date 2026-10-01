-- Vacancies table
CREATE TABLE IF NOT EXISTS vacancies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id TEXT NOT NULL,  -- ID of vacancy in HH.ru, Telegram channels or other sources

    source TEXT NOT NULL,  -- Such as HH.ru, LinkedIn, Telegram
    title TEXT NOT NULL,
    company TEXT,

    salary_text TEXT,
    salary_from INT,
    salary_to INT,
    currency VARCHAR(3),  -- USD, RUB, CNY

    grade grade NOT NULL,  -- Intern/Junior/Senior and etc
    employment_type employment_type NOT NULL,

    location TEXT,
    country TEXT,
    city TEXT,

    description TEXT NOT NULL,
    url TEXT NOT NULL,

    published_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    parsed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_vacancies_source ON vacancies(source);
CREATE INDEX IF NOT EXISTS idx_vacancies_company ON vacancies(company);
CREATE INDEX IF NOT EXISTS idx_vacancies_parsed_at ON vacancies(parsed_at);

CREATE INDEX IF NOT EXISTS idx_vacancies_published_at ON vacancies(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_vacancies_salary ON vacancies(currency, salary_from, salary_to);
CREATE INDEX IF NOT EXISTS idx_vacancies_filters ON vacancies(employment_type, grade);

CREATE INDEX IF NOT EXISTS idx_vacancies_city ON vacancies(city);