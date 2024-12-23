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


def test_mmr_prefers_diverse_results():
    # three near-duplicates and one different but slightly less relevant track
    hits = [
        _hit(1, "a", 0.90, [1, 0]),
        _hit(2, "b", 0.89, [1, 0.01]),
        _hit(3, "c", 0.88, [1, 0.02]),
        _hit(4, "d", 0.80, [0, 1]),
    ]
    picked = [h.track.id for h in mmr_select(hits, k=2, diversity=0.5)]
    assert picked == ["t1", "t4"]


def test_mmr_skips_ids_and_duplicate_titles():
    hits = [_hit(1, "a", 0.9, [1, 0]), _hit(2, "b", 0.8, [0, 1])]
    hits.append(_hit(3, "a", 0.85, [1, 0.1]))
    hits[2].track.name = hits[0].track.name  # same song, different release
    picked = mmr_select(hits, k=5, skip_ids={"t2"})
    assert [h.track.id for h in picked] == ["t1"]


class FakeHarvester:
    def __init__(self, store, tracks):
        self.store, self.tracks, self.calls = store, tracks, 0

    def run(self, tasks):
        self.calls += 1
        return self.store.upsert(self.tracks)


def _catalog():
    tracks = []
    for i in range(30):
        tracks.append(
            make_track(i, f"study beat {i}", f"lofi{i % 10}", genres=["lo-fi"], tags=["lo-fi", "studying"])
        )
    for i in range(30, 60):
        tracks.append(make_track(i, f"banger {i}", f"metal{i % 10}", genres=["metal"], tags=["metal", "gym"]))
    return tracks


def test_recommender_harvests_when_catalog_is_empty(store, embedder):
    harvester = FakeHarvester(store, _catalog())
    rec = Recommender(store, embedder, lambda: harvester, min_good_hits=10, good_hit_score=0.2)

    result = rec.recommend("lo-fi for studying", size=8)

    assert harvester.calls == 1
    assert result.harvested == 60
    assert len(result.main) == 8
    assert all("lo-fi" in t.genres for t in result.main)
    assert not {t.id for t in result.main} & {t.id for t in result.alternative}


def test_recommender_skips_harvest_when_catalog_is_good(store, embedder):
    store.upsert(_catalog())
    harvester = FakeHarvester(store, [])
    rec = Recommender(store, embedder, lambda: harvester, min_good_hits=5, good_hit_score=0.2)

    result = rec.recommend("metal for the gym", size=5)

    assert harvester.calls == 0
    assert all("metal" in t.genres for t in result.main)


def test_explicit_filter(store, embedder):
    store.upsert([
        make_track(1, "clean", "x", genres=["rock"]),
        make_track(2, "dirty", "y", genres=["rock"], explicit=True),
    ])
    rec = Recommender(store, embedder, lambda: FakeHarvester(store, []), min_good_hits=0)
    result = rec.recommend("rock", size=5, allow_explicit=False)
    assert [t.id for t in result.main] == ["t1"]
