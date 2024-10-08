"""Turns a free-text prompt into Spotify search queries.

There's no dataset behind the app, so the catalog is built from Spotify search
results. Spotify search is keyword based and doesn't understand
"chill rock music for studying", so we pull out the parts it does understand:
genres (genre:"rock"), decades (year:1990-1999) and plain keywords.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Not exhaustive, just the genres people actually type. Spotify's genre filter
# matches artist genres, so multi-word ones need quoting.
GENRES = {
    "acoustic", "afrobeat", "alt-rock", "alternative", "ambient", "blues", "bossa nova",
    "classical", "country", "dance", "deep house", "disco", "drum and bass", "dubstep",
    "edm", "electro", "electronic", "emo", "folk", "funk", "garage", "gospel", "grunge",
    "hard rock", "hardcore", "heavy metal", "hip hop", "house", "indie", "indie pop",
    "indie rock", "industrial", "j-pop", "jazz", "k-pop", "latin", "lo-fi", "metal",
    "neo soul", "new wave", "opera", "phonk", "piano", "pop", "pop punk", "post-rock",
    "psychedelic", "punk", "r&b", "rap", "reggae", "reggaeton", "rock", "salsa",
    "shoegaze", "singer-songwriter", "ska", "soul", "soundtrack", "synthwave", "techno",
    "trance", "trap", "trip hop", "chillwave", "dream pop", "bedroom pop", "math rock",
    "drill", "grime", "afrobeats", "amapiano", "city pop", "flamenco", "tango",
}

# People describe activities and moods, not genres. Map the common ones to
# genres that usually fit - this is the "taste" part and it's opinionated.
MOOD_HINTS = {
    "study": ["lo-fi", "ambient", "classical", "post-rock"],
    "studying": ["lo-fi", "ambient", "classical", "post-rock"],
    "focus": ["ambient", "lo-fi", "post-rock"],
    "work": ["lo-fi", "chillwave", "ambient"],
    "coding": ["synthwave", "lo-fi", "electronic"],
    "sleep": ["ambient", "piano", "classical"],
    "chill": ["chillwave", "lo-fi", "dream pop", "indie"],
    "relax": ["ambient", "acoustic", "neo soul"],
    "gym": ["hip hop", "edm", "phonk", "trap"],
    "workout": ["hip hop", "edm", "phonk", "trap"],
    "running": ["edm", "dance", "pop"],
    "party": ["dance", "house", "pop", "reggaeton"],
    "sad": ["singer-songwriter", "indie", "acoustic"],
    "happy": ["pop", "funk", "disco"],
    "romantic": ["r&b", "soul", "neo soul"],
    "love": ["r&b", "soul", "pop"],
    "angry": ["metal", "hardcore", "punk"],
    "roadtrip": ["rock", "indie rock", "country"],
    "driving": ["synthwave", "rock", "indie rock"],
    "night": ["synthwave", "trip hop", "r&b"],
    "morning": ["acoustic", "indie pop", "folk"],
    "summer": ["reggaeton", "pop", "house"],
    "rainy": ["trip hop", "jazz", "lo-fi"],
    "dinner": ["jazz", "bossa nova", "soul"],
    "cooking": ["funk", "soul", "bossa nova"],
    "gaming": ["synthwave", "electronic", "dubstep"],
}

ALIASES = {
    "hiphop": "hip hop", "hip-hop": "hip hop", "rnb": "r&b", "lofi": "lo-fi",
    "lo fi": "lo-fi", "dnb": "drum and bass", "electronica": "electronic",
    "metalcore": "metal", "indie-rock": "indie rock", "synth": "synthwave",
    "classic rock": "rock",
}

STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "to", "of", "in", "on", "with", "my", "me",
    "i", "some", "songs", "song", "music", "playlist", "tracks", "track", "vibes",
    "vibe", "like", "that", "is", "are", "while", "when", "good", "best", "give",
    "make", "create", "please", "want", "need", "something", "stuff", "kind", "type",
}

_DECADE = re.compile(r"\b(?:19|20)?([0-9])0'?s\b")


@dataclass
class SearchTask:
    kind: str           # "track" or "artist"
    query: str
    tags: list[str] = field(default_factory=list)
    limit: int = 30


@dataclass
class ParsedPrompt:
    raw: str
    genres: list[str]
    hinted_genres: list[str]
    keywords: list[str]
    year_range: str | None


def _normalize(text: str) -> str:
    text = text.lower().strip()
    for alias, canonical in ALIASES.items():
        text = re.sub(rf"\b{re.escape(alias)}\b", canonical, text)
    return text


def _decade_to_range(match: re.Match) -> str:
    full = match.group(0)
    digit = int(match.group(1))
    # "90s" -> 1990s, "2010s" -> 2010s, "00s" -> 2000s
    if full.startswith("20") or (len(full.rstrip("'s")) == 2 and digit <= 2):
        start = 2000 + digit * 10
    else:
        start = 1900 + digit * 10
    return f"{start}-{start + 9}"


def parse_prompt(prompt: str) -> ParsedPrompt:
    text = _normalize(prompt)

    year_range = None
    decade = _DECADE.search(text)
    if decade:
        year_range = _decade_to_range(decade)
        text = text.replace(decade.group(0), " ")

    # longest genres first so "indie rock" wins over "rock"
    genres = []
    for genre in sorted(GENRES, key=len, reverse=True):
        pattern = rf"(?<![\w-]){re.escape(genre)}(?![\w-])"
        if re.search(pattern, text):
            genres.append(genre)
            text = re.sub(pattern, " ", text)

    words = [w for w in re.findall(r"[a-z0-9&'-]+", text) if w not in STOPWORDS and len(w) > 1]

    hinted = []
    for word in words:
        for genre in MOOD_HINTS.get(word, []):
            if genre not in genres and genre not in hinted:
                hinted.append(genre)

    return ParsedPrompt(raw=prompt.strip(), genres=genres, hinted_genres=hinted, keywords=words, year_range=year_range)


def build_search_plan(parsed: ParsedPrompt, budget: int = 8) -> list[SearchTask]:
    """At most `budget` searches - each one is up to 3 API calls (10 per page)."""
    year = f" year:{parsed.year_range}" if parsed.year_range else ""
    mood_tags = [w for w in parsed.keywords if w in MOOD_HINTS]
    tasks: list[SearchTask] = []

    # explicit genres are the strongest signal
    for genre in parsed.genres:
        tasks.append(SearchTask("track", f'genre:"{genre}"{year}', tags=[genre, *mood_tags], limit=40))
        tasks.append(SearchTask("artist", f'genre:"{genre}"', tags=[genre, *mood_tags], limit=10))

    # genres inferred from mood words only fill whatever budget is left
    hinted = parsed.hinted_genres if not parsed.genres else parsed.hinted_genres[:2]
    for genre in hinted:
        tasks.append(SearchTask("track", f'genre:"{genre}"{year}', tags=[genre, *mood_tags], limit=30))

    # plain keyword search catches titles like "Rainy Day" or "Midnight Drive"
    if parsed.keywords:
        tasks.append(SearchTask("track", " ".join(parsed.keywords[:5]) + year, tags=mood_tags, limit=30))

    if not tasks:  # prompt was only stopwords / nonsense - just search it raw
        tasks.append(SearchTask("track", parsed.raw[:100], limit=30))

    return tasks[:budget]
