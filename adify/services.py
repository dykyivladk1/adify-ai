"""Process-wide singletons. The embedding model and the Qdrant client are
expensive, so build them once per worker and reuse."""
from functools import lru_cache

from .auth import app_client
from .config import settings
from .embeddings import SentenceEmbedder
from .harvester import Harvester
from .models import Track
from .recommender import Recommender
from .spotify_client import SpotifyClient
from .vector_store import TrackStore


@lru_cache(maxsize=1)
def get_embedder() -> SentenceEmbedder:
    return SentenceEmbedder(settings.embedding_model)


@lru_cache(maxsize=1)
def get_store() -> TrackStore:
    return TrackStore.from_settings(settings, get_embedder())


@lru_cache(maxsize=1)
