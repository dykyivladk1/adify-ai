import pytest

from adify import create_app, routes
from adify.prompt_parser import parse_prompt
from adify.recommender import Recommendation
from tests.conftest import make_track


class StubRecommender:
    def recommend(self, prompt, size=25, allow_explicit=True, refresh=False):
        main = [make_track(i, f"song {i}", f"artist{i}") for i in range(3)]
        alt = [make_track(i, f"song {i}", f"artist{i}") for i in range(3, 5)]
        return Recommendation(prompt, parse_prompt(prompt), main, alt, harvested=5)


@pytest.fixture
