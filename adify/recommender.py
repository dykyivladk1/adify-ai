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
