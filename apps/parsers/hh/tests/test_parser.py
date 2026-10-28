from parser import clean_text, clean_vacancy_url, extract_external_id


def test_clean_text_normalizes_spaces():
    value = "от\u202f100\u202f000\xa0₽   за месяц"
    assert clean_text(value) == "от 100 000 ₽ за месяц"


def test_clean_vacancy_url_removes_query():
    url = "https://hh.ru/vacancy/123?query=python&from=search"
    assert clean_vacancy_url(url) == "https://hh.ru/vacancy/123"


def test_extract_external_id():
    assert extract_external_id("https://hh.ru/vacancy/123") == "123"
    assert extract_external_id("https://hh.ru/employer/123") is None
