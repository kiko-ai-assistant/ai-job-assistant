from habr_parser.description import html_to_text, truncate_text


def test_blocks_and_list_items_go_on_separate_lines():
    html = "<p>Обязанности:</p><ul><li>Писать код</li><li>Ревьюить</li></ul><p>Итого</p>"

    assert html_to_text(html) == "Обязанности:\n• Писать код\n• Ревьюить\nИтого"


def test_line_breaks_entities_and_blank_lines_are_normalised():
    html = "<div>a&nbsp;&amp;&nbsp;b<br>c</div>\n\n   <div>   </div><p>d</p>"

    assert html_to_text(html) == "a & b\nc\nd"


def test_text_within_the_limit_is_untouched():
    assert truncate_text("short text", limit=50) == "short text"


def test_long_text_is_cut_at_a_word_boundary_within_the_limit():
    text = "word " * 100

    result = truncate_text(text, limit=52)

    assert len(result) <= 52
    assert result.endswith("…")
    assert result.removesuffix("…").split(" ")[-1] == "word"


def test_text_without_spaces_is_hard_cut():
    result = truncate_text("x" * 100, limit=10)

    assert result == "x" * 9 + "…"
