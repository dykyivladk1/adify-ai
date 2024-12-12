from adify.prompt_parser import build_search_plan, parse_prompt


def test_detects_genres_and_moods():
    parsed = parse_prompt("Chill rock music for studying")
    assert parsed.genres == ["rock"]
    assert "lo-fi" in parsed.hinted_genres
    assert parsed.keywords == ["chill", "studying"]


def test_longer_genre_wins():
    parsed = parse_prompt("some indie rock please")
    assert parsed.genres == ["indie rock"]


def test_aliases_and_decades():
    parsed = parse_prompt("90s hiphop")
    assert parsed.genres == ["hip hop"]
    assert parsed.year_range == "1990-1999"

    assert parse_prompt("2010s pop").year_range == "2010-2019"
    assert parse_prompt("00s emo").year_range == "2000-2009"
    assert parse_prompt("80's synthwave").year_range == "1980-1989"


def test_genre_inside_other_word_is_ignored():
    assert parse_prompt("popular songs").genres == []


def test_plan_uses_genre_filters_and_year():
    plan = build_search_plan(parse_prompt("80s rock for driving"))
    queries = [t.query for t in plan]
    assert 'genre:"rock" year:1980-1989' in queries
    assert any(t.kind == "artist" for t in plan)
    assert len(plan) <= 8


def test_plan_for_garbage_prompt_still_searches():
    plan = build_search_plan(parse_prompt("the and for"))
    assert len(plan) == 1
