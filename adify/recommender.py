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


