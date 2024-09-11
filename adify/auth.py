from flask import session
from spotipy.cache_handler import FlaskSessionCacheHandler
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

from .config import settings
from .spotify_client import SpotifyClient


def user_oauth() -> SpotifyOAuth:
    # Token lives in the (signed) Flask session cookie, so every visitor gets their own.
    return SpotifyOAuth(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        redirect_uri=settings.spotify_redirect_uri,
        scope=settings.spotify_scopes,
        cache_handler=FlaskSessionCacheHandler(session),
        show_dialog=False,
    )


def is_logged_in() -> bool:
    oauth = user_oauth()
    return oauth.validate_token(oauth.cache_handler.get_cached_token()) is not None


def user_client() -> SpotifyClient:
    oauth = user_oauth()

    def token() -> str:
        info = oauth.validate_token(oauth.cache_handler.get_cached_token())
        if not info:
            raise PermissionError("Spotify session expired, please log in again")
        return info["access_token"]

    return SpotifyClient(token)


_app_credentials: SpotifyClientCredentials | None = None


def app_client() -> SpotifyClient:
    """Client-credentials client. Enough for search/artists/albums, no user scopes."""
    global _app_credentials
    if _app_credentials is None:
        _app_credentials = SpotifyClientCredentials(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret,
        )
    return SpotifyClient(lambda: _app_credentials.get_access_token(as_dict=False))
