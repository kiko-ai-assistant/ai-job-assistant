from dataclasses import dataclass


@dataclass(frozen=True)
class SearchTarget:
    name: str
    group: str
    keywords: str | None = None
    professional_roles: tuple[int, ...] = ()
    max_pages: int = 1


# IDs below are taken from the current HH vacancy filter URLs/results.
# Keep them in one place so they are easy to update if HH changes the catalog.
SEARCH_TARGETS: tuple[SearchTarget, ...] = (
    SearchTarget(
        name="it_core",
        group="it",
        professional_roles=(
            96,   # Программист, разработчик
            124,  # Тестировщик
            160,  # DevOps-инженер
            165,  # Дата-сайентист
            156,  # BI-аналитик, аналитик данных
            148,  # Системный аналитик
            150,  # Бизнес-аналитик
            116,  # Специалист по информационной безопасности
            112,  # Сетевой инженер
            113,  # Системный администратор
            114,  # Системный инженер
            121,  # Специалист технической поддержки
            126,  # Технический писатель
            104,  # Руководитель группы разработки
        ),
        max_pages=3,
    ),
    SearchTarget(
        name="management",
        group="management",
        professional_roles=(
            73,   # Менеджер продукта
            107,  # Руководитель проектов
            157,  # Руководитель отдела аналитики
            125,  # Технический директор (CTO)
            36,   # Директор по информационным технологиям (CIO)
        ),
        max_pages=2,
    ),
    # Marketing IDs are deliberately not guessed. These narrow keyword targets
    # reduce load while remaining easy to change once the team agrees on exact
    # HH professional-role IDs for marketing.
    SearchTarget(
        name="marketing_marketer",
        group="marketing",
        keywords="маркетолог",
        max_pages=1,
    ),
    SearchTarget(
        name="marketing_smm",
        group="marketing",
        keywords="SMM",
        max_pages=1,
    ),
    SearchTarget(
        name="marketing_brand",
        group="marketing",
        keywords="бренд-менеджер",
        max_pages=1,
    ),
)


def enabled_targets(groups: tuple[str, ...]) -> list[SearchTarget]:
    selected = set(groups)
    return [target for target in SEARCH_TARGETS if target.group in selected]
