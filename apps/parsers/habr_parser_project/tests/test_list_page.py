from habr_parser.list_page import extract_vacancy_ids
from tests.builders import make_list_html


def test_ids_are_returned_in_page_order_without_duplicates():
    html = make_list_html([300, 100, 200, 100])

    assert extract_vacancy_ids(html) == ["300", "100", "200"]


def test_links_that_are_not_vacancies_are_ignored():
    html = (
        '<a href="/vacancies?page=2">next</a>'
        '<a href="/companies/acme">company</a>'
        '<a href="/vacancies/remote">category</a>'
        '<a href="/vacancies/42">ok</a>'
    )

    assert extract_vacancy_ids(html) == ["42"]


def test_absolute_urls_query_strings_and_nested_paths_are_understood():
    html = (
        '<a href="https://career.habr.com/vacancies/7">a</a>'
        '<a href="/vacancies/8?from=list">b</a>'
        '<a href="/vacancies/9/response">c</a>'
    )

    assert extract_vacancy_ids(html) == ["7", "8", "9"]


def test_empty_page_gives_no_ids():
    assert extract_vacancy_ids("<html><body>nothing here</body></html>") == []
