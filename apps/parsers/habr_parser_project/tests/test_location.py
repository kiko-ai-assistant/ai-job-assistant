from habr_parser.location import build_location


def place(**address):
    return {"@type": "Place", "address": {"@type": "PostalAddress", **address}}


def test_city_and_country():
    location = build_location(place(addressLocality="Москва", addressCountry="RU"))

    assert (location.city, location.country) == ("Москва", "RU")
    assert location.text == "Москва, RU"


def test_country_only():
    location = build_location(place(addressCountry="Беларусь"))

    assert (location.city, location.country, location.text) == (None, "Беларусь", "Беларусь")


def test_city_without_country_is_kept_only_in_text():
    # the validator rejects a city without a country
    location = build_location(place(addressLocality="Москва"))

    assert (location.city, location.country) == (None, None)
    assert location.text == "Москва"


def test_first_place_of_a_list_is_used():
    location = build_location(
        [place(addressLocality="Минск", addressCountry="BY"), place(addressLocality="Москва")]
    )

    assert location.city == "Минск"


def test_country_may_be_an_object_with_a_name():
    location = build_location(
        place(addressLocality="Минск", addressCountry={"@type": "Country", "name": "Belarus"})
    )

    assert location.country == "Belarus"


def test_plain_string_address_becomes_text():
    assert build_location({"address": "Санкт-Петербург"}).text == "Санкт-Петербург"


def test_nothing_usable_gives_none():
    assert build_location(None) is None
    assert build_location({}) is None
    assert build_location(place()) is None
