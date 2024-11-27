"""Warm up the Qdrant catalog so the first users don't wait on Spotify.

    python -m scripts.seed_index                 # default moods/genres
    python -m scripts.seed_index "jazz" "90s rap"  # your own prompts

Uses client credentials, no user login needed.
"""
import logging
import sys
import time

from adify.config import settings
from adify.prompt_parser import build_search_plan, parse_prompt
from adify.services import get_harvester, get_store

DEFAULT_PROMPTS = [
    "chill lo-fi for studying",
    "indie rock road trip",
    "90s hip hop",
    "sad acoustic songs",
    "house music party",
    "synthwave night drive",
    "jazz for dinner",
    "workout phonk and trap",
    "ambient music for sleep",
    "happy summer pop",
    "classic soul and funk",
    "heavy metal",
    "r&b love songs",
    "reggaeton summer",
    "techno",
    "folk morning coffee",
]


def main(prompts: list[str]) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings.validate()

    store = get_store()
    harvester = get_harvester()
    print(f"catalog size before: {store.count()}")

    for i, prompt in enumerate(prompts, 1):
        started = time.perf_counter()
        added = harvester.run(build_search_plan(parse_prompt(prompt), budget=10))
        print(f"[{i}/{len(prompts)}] {prompt!r}: {added} tracks in {time.perf_counter() - started:.1f}s")

    print(f"catalog size after: {store.count()}")


if __name__ == "__main__":
    main(sys.argv[1:] or DEFAULT_PROMPTS)
