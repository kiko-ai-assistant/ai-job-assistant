from config import SearchConfig
from roles import SearchTarget
from search_urls import build_search_url


def test_build_search_url_repeats_professional_role():
    target = SearchTarget(
        name="test",
        group="it",
        keywords="python",
        professional_roles=(96, 124),
        max_pages=1,
    )
    config = SearchConfig(area="1", employment="full")

    url = build_search_url("https://hh.ru", target, 2, config)

    assert "page=2" in url
    assert "text=python" in url
    assert "area=1" in url
    assert "employment=full" in url
    assert "professional_role=96" in url
    assert "professional_role=124" in url
