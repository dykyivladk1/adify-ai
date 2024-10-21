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
def get_harvester() -> Harvester:
    return Harvester(app_client(), get_store())


@lru_cache(maxsize=1)
def get_recommender() -> Recommender:
    return Recommender(
        store=get_store(),
        embedder=get_embedder(),
        harvester_factory=get_harvester,
        min_good_hits=settings.min_good_hits,
        good_hit_score=settings.good_hit_score,
        max_per_artist=settings.max_tracks_per_artist,
    )


def save_playlist(client: SpotifyClient, name: str, description: str, tracks: list[Track], public: bool = True) -> dict:
    playlist = client.create_playlist(name, description, public=public)
    client.add_to_playlist(playlist["id"], [t.uri for t in tracks])
    return {
        "id": playlist["id"],
        "name": playlist.get("name", name),
        "url": playlist.get("external_urls", {}).get("spotify", f"https://open.spotify.com/playlist/{playlist['id']}"),
        "tracks": len(tracks),
    }
