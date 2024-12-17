import numpy as np

from adify.recommender import Recommender, mmr_select
from adify.vector_store import Hit
from tests.conftest import make_track


def _hit(i, artist, score, vec):
    v = np.asarray(vec, dtype=np.float32)
    return Hit(make_track(i, f"song {i}", artist), score, v / np.linalg.norm(v))


