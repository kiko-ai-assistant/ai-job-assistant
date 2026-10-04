import re

VACANCY_KEYWORDS = [
    r"вакансия",
    r"требуется",
    r"ищем",
    r"hiring",
    r"developer",
    r"разработчик",
    r"инженер",
    r"lead",
    r"senior",
    r"middle",
    r"junior",
]

SALARY_PATTERNS = [
    r"(\d[\d\s]{2,}\s*(?:до|от|-)?\s*\d*[\d\s]{2,}?\s*(?:руб|rub|usd|\$|eur|€|k|к|тыс))",
    r"(\$\s*\d+[\d\s]*(?:-\s*\$?\s*\d+[\d\s]*)?)",
    r"((?:от|до)\s*\d+[\d\s]*(?:руб|rub|\$|eur|k))",
]

TITLE_ROLE_KEYWORDS = [
    "developer",
    "разработчик",
    "инженер",
    "lead",
    "senior",
    "middle",
    "junior",
    "teamlead",
]


class HeuristicExtractor:
    @staticmethod
    def is_vacancy(text: str) -> bool:
        lower = text.lower()
        if len(text.strip()) < 40:
            return False
        # Filter obvious non-vacancies
        if any(bad in lower for bad in ["реклама", "партнерский материал", "подписывайтесь на"]):
            if "вакансия" not in lower and "требуется" not in lower:
                return False
        return any(re.search(kw, lower) for kw in VACANCY_KEYWORDS)

    @staticmethod
    def extract_title(text: str) -> str:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[:3]:
            # Remove emoji and formatting artifacts
            cleaned = re.sub(r"[#*`_]", "", line).strip()
            if any(re.search(kw, cleaned.lower()) for kw in TITLE_ROLE_KEYWORDS):
                return cleaned[:100]
        return lines[0][:100] if lines else "Вакансия"

    @staticmethod
    def extract_salary(text: str) -> str | None:
        for pattern in SALARY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    @staticmethod
    def extract_company(text: str) -> str | None:
        pattern = r"(?:компания|в\s+компанию|в)\s+([A-ZА-Я][A-Za-zА-Яа-я0-9\s\-]{2,30})"
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        return None
