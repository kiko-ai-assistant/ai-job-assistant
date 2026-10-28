import json
from pathlib import Path

from models import Vacancy


def save_json(
    vacancies: list[Vacancy],
    path: str = "output/vacancies.json",
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        json.dumps(
            [vacancy.to_dict() for vacancy in vacancies],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
