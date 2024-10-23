import logging

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from . import auth
from .config import settings
from .recommender import Recommendation
from .services import get_recommender, get_store, save_playlist
from .spotify_client import SpotifyError

log = logging.getLogger(__name__)
bp = Blueprint("adify", __name__)

MAX_PROMPT_LEN = 200


def _flag(data, key: str, default: bool) -> bool:
    if key not in data:
        return default
    return str(data.get(key)).lower() in ("on", "true", "1")


def _read_options(data, is_form: bool) -> dict:
    # HTML forms simply don't send unchecked checkboxes, so for forms a missing
    # key means "off". For JSON a missing key means "use the default".
    default = not is_form
    prompt = (data.get("prompt") or "").strip()[:MAX_PROMPT_LEN]
    try:
        size = int(data.get("size") or settings.playlist_size)
    except (TypeError, ValueError):
        size = settings.playlist_size
    return {
        "prompt": prompt,
        "size": max(5, min(size, 50)),
        "allow_explicit": _flag(data, "explicit", default),
        "two_playlists": _flag(data, "two_playlists", default),
        "save": _flag(data, "save", False),
        "public": _flag(data, "public", default),
    }


