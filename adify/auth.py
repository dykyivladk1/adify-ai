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


