import pytest

from adify import create_app, routes
from adify.prompt_parser import parse_prompt
from adify.recommender import Recommendation
from tests.conftest import make_track


