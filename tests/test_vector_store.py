from tests.conftest import make_track


def test_upsert_merges_tags(store):
    store.upsert([make_track(1, "song", "a", tags=["chill"])])
    store.upsert([make_track(1, "song", "a", tags=["study"])])

    assert store.count() == 1
    hit = store.search(store.embedder.encode(["song"])[0], limit=1)[0]
    assert hit.track.tags == ["chill", "study"]
