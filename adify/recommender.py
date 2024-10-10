from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from .embeddings import Embedder
from .harvester import Harvester
from .models import Track
from .prompt_parser import ParsedPrompt, build_search_plan, parse_prompt
from .vector_store import Hit, TrackStore

log = logging.getLogger(__name__)


@dataclass
class Recommendation:
    prompt: str
    parsed: ParsedPrompt
    main: list[Track]
    alternative: list[Track]
    harvested: int = 0
    scores: dict[str, float] = field(default_factory=dict)


def query_text(parsed: ParsedPrompt) -> str:
    # Mirror the structure of Track.document() so the prompt lands closer to
    # the track texts in embedding space than the bare sentence would.
    parts = [parsed.raw]
    genres = parsed.genres + parsed.hinted_genres
    if genres:
        parts.append(f"genres: {', '.join(genres)}")
    if parsed.keywords:
        parts.append(f"vibe: {', '.join(parsed.keywords)}")
    return ". ".join(parts)


def mmr_select(
    hits: list[Hit],
    k: int,
    diversity: float = 0.3,
    max_per_artist: int = 2,
    skip_ids: set[str] | None = None,
) -> list[Hit]:
    """Maximal marginal relevance: trade relevance against similarity to what's
    already picked, so we don't return 25 near-identical tracks."""
    skip_ids = skip_ids or set()
    candidates = [h for h in hits if h.track.id not in skip_ids]
    if not candidates:
        return []

    vectors = np.stack([h.vector for h in candidates])
    relevance = np.array([h.score for h in candidates])
    used = np.zeros(len(candidates), dtype=bool)
    max_sim = np.zeros(len(candidates))
    selected: list[int] = []
    per_artist: dict[str, int] = {}
    seen_titles: set[tuple[str, str]] = set()

    while len(selected) < k:
        mmr = (1 - diversity) * relevance - diversity * max_sim
        mmr[used] = -np.inf
        best = int(np.argmax(mmr))
        if not np.isfinite(mmr[best]):
            break  # ran out of candidates
        used[best] = True

        track = candidates[best].track
        # same song released as single + album track shows up under two ids
        title_key = (track.name.lower(), track.main_artist_id)
        if per_artist.get(track.main_artist_id, 0) >= max_per_artist or title_key in seen_titles:
            continue

        selected.append(best)
        per_artist[track.main_artist_id] = per_artist.get(track.main_artist_id, 0) + 1
        seen_titles.add(title_key)
        max_sim = np.maximum(max_sim, vectors @ vectors[best])

    return [candidates[i] for i in selected]


