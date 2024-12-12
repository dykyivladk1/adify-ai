from adify.prompt_parser import build_search_plan, parse_prompt


def test_detects_genres_and_moods():
    parsed = parse_prompt("Chill rock music for studying")
    assert parsed.genres == ["rock"]
    assert "lo-fi" in parsed.hinted_genres
    assert parsed.keywords == ["chill", "studying"]


