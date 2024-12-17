import numpy as np

from adify.recommender import Recommender, mmr_select
from adify.vector_store import Hit
from tests.conftest import make_track


def _hit(i, artist, score, vec):
    v = np.asarray(vec, dtype=np.float32)
    return Hit(make_track(i, f"song {i}", artist), score, v / np.linalg.norm(v))


def test_mmr_caps_tracks_per_artist():
    hits = [_hit(i, "same", 0.9 - i * 0.01, [1, i * 0.01]) for i in range(5)]
    hits += [_hit(10 + i, f"other{i}", 0.5, [0.5, 1]) for i in range(5)]
    picked = mmr_select(hits, k=6, max_per_artist=2)
    assert len(picked) == 6
    assert sum(h.track.artists[0] == "same" for h in picked) == 2


