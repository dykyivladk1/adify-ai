from adify.harvester import Harvester, track_from_api
from adify.prompt_parser import SearchTask


def _api_track(i, artist_id="a1"):
    return {
        "id": f"t{i}",
        "name": f"Song {i}",
        "artists": [{"id": artist_id, "name": artist_id.upper()}],
        "album": {"name": "Album", "release_date": "1994-05-01"},
        "explicit": False,
    }


