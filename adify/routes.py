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


