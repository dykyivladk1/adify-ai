import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw else default


@dataclass(frozen=True)
class Settings:
    spotify_client_id: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    spotify_client_secret: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    spotify_redirect_uri: str = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5000/callback")
    spotify_scopes: str = "playlist-modify-public playlist-modify-private"

    # Either point to a running Qdrant server (docker compose up qdrant) or leave
    # QDRANT_URL empty and the client will run embedded, persisting to QDRANT_PATH.
    qdrant_url: str = os.getenv("QDRANT_URL", "")
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    qdrant_path: str = os.getenv("QDRANT_PATH", "./qdrant_data")
    collection: str = os.getenv("QDRANT_COLLECTION", "tracks")

    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    playlist_size: int = _env_int("PLAYLIST_SIZE", 25)
    # How many tracks we want the catalog to have "close enough" to a prompt
    # before we stop hitting Spotify for more.
    min_good_hits: int = _env_int("MIN_GOOD_HITS", 60)
    good_hit_score: float = float(os.getenv("GOOD_HIT_SCORE", "0.45"))
    max_tracks_per_artist: int = _env_int("MAX_TRACKS_PER_ARTIST", 2)

    secret_key: str = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")

    def validate(self) -> None:
        missing = [
            name
            for name, value in (
                ("SPOTIFY_CLIENT_ID", self.spotify_client_id),
                ("SPOTIFY_CLIENT_SECRET", self.spotify_client_secret),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing env vars: {', '.join(missing)} (see .env.example)")


settings = Settings()
