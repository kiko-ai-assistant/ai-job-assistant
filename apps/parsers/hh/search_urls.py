from urllib.parse import urlencode

from config import SearchConfig
from roles import SearchTarget


def build_search_url(
    base_url: str,
    target: SearchTarget,
    page: int,
    config: SearchConfig,
) -> str:
    params: list[tuple[str, str | int]] = [("page", page)]

    if target.keywords:
        params.append(("text", target.keywords))

    if config.area:
        params.append(("area", config.area))

    if config.employment:
        params.append(("employment", config.employment))

    for role_id in target.professional_roles:
        params.append(("professional_role", role_id))

    return f"{base_url.rstrip('/')}/search/vacancy?{urlencode(params)}"
