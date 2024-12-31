# ADIFY AI - Spotify Playlist Generator

Type a mood or activity ("chill rock music for studying"), get two Spotify playlists back: a **closest match** and a **wider mix**.

The first version shipped with a prebuilt song dataset and a FAISS index. This one needs neither: the catalog grows on its own in **Qdrant** as people use the app.

## How it works

```
prompt ──► parse (genres, moods, decade, keywords)
       ──► embed (sentence-transformers) ──► Qdrant search
                                             │
              not enough good hits? ◄────────┘
                     │ yes
                     ▼
         Spotify search: genre:"x" year:..., artists → albums → tracks
                     │
                     ▼
         embed track text ──► upsert into Qdrant ──► search again
                                                     │
                                                     ▼
                         MMR re-rank (diversity + max N per artist)
                                                     │
                                  ┌──────────────────┴──────────────────┐
                                  ▼                                     ▼
                           Closest match                           Wider mix
                                  └──────────► POST /me/playlists ◄─────┘
```

- **No dataset.** Every track in the index came from a Spotify search that some prompt triggered. A new mood takes ~10-20s the first time, then it's served from Qdrant.
- **Track text** that gets embedded looks like `Midnight City by M83. from the album Hurry Up, We're Dreaming. released 2011. genres: electronic, synthwave. vibe: synthwave, driving`. The "vibe" tags pile up over time as the same track shows up for different searches.
- **Mood → genre hints** (`prompt_parser.py`) map things like "studying" or "gym" to genres Spotify's search actually understands. It's opinionated, tweak it.
- **Two playlists**: the second one excludes everything from the first, uses stronger diversity and only 1 track per artist.

### Spotify API notes (Feb 2026 dev-mode changes)

The client is written against the current API, which matters because a lot of tutorials are out of date:

- Search returns **max 10 results per page**, so the client pages with `offset`.
- Playlists are created with `POST /me/playlists` and filled with `POST /playlists/{id}/items`.
- Track contents of playlists you don't own aren't readable anymore, and top-tracks / recommendations / audio-features are gone. That's why harvesting goes search → artists → albums → album tracks.
- Dev-mode apps need the owner to have **Spotify Premium**, and only users added under *User Management* in the dashboard (max 5) can log in.

## Setup

1. Create an app at <https://developer.spotify.com/dashboard> (Web API). Add redirect URI `http://127.0.0.1:5000/callback`. Spotify doesn't accept `localhost`, it has to be the loopback IP.
2. Configure:

```bash
cp .env.example .env   # fill SPOTIFY_CLIENT_ID / SECRET and FLASK_SECRET_KEY
```

### Option A: Docker (Qdrant + app)

```bash
docker compose up --build
```

Open <http://127.0.0.1:5000>.

### Option B: local Python

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# Qdrant as a server...
docker compose up -d qdrant
export QDRANT_URL=http://127.0.0.1:6333
# ...or leave QDRANT_URL empty and Qdrant runs embedded, stored in ./qdrant_data

python wsgi.py
```

Embedded Qdrant locks its folder, so only one process can use it. For gunicorn with several workers, use the Qdrant server.

### Warm up the catalog (optional)

The first prompts are slow on an empty index. Pre-fill it with ~16 common moods/genres (takes a few minutes):

```bash
python -m scripts.seed_index
python -m scripts.seed_index "k-pop" "70s disco" "drum and bass for running"
```

## API

```bash
curl -X POST http://127.0.0.1:5000/api/generate \
  -H 'Content-Type: application/json' \
  -d '{"prompt": "rainy sunday jazz", "size": 20}'
```

| field           | default | notes                                         |
|-----------------|---------|-----------------------------------------------|
| `prompt`        | -       | required, max 200 chars                       |
| `size`          | 25      | 5-50                                          |
| `explicit`      | true    | false filters explicit tracks                 |
| `two_playlists` | true    |                                               |
| `save`          | false   | true creates the playlists; needs browser login session |
| `public`        | true    |                                               |

`GET /health` returns how many tracks are indexed.

## Project layout

```
adify/
  config.py          env settings
  auth.py            spotipy OAuth (per-user, stored in session) + client credentials
  spotify_client.py  small requests-based Web API client, retries on 429
  prompt_parser.py   prompt -> genres / moods / decade -> search plan
  harvester.py       runs the search plan, builds Track objects, upserts to Qdrant
  vector_store.py    Qdrant collection wrapper
  embeddings.py      lazy sentence-transformers wrapper
  recommender.py     retrieval + MMR re-ranking into two playlists
  routes.py          Flask views + JSON API
scripts/seed_index.py
tests/               pytest, uses in-memory Qdrant + a hashing embedder
```

## Tests

```bash
pytest
```

Tests don't hit Spotify or download the model.

## Config

All in `.env`, see `.env.example`. Ones worth tuning:

- `MIN_GOOD_HITS` / `GOOD_HIT_SCORE`: when the catalog is "good enough" to skip Spotify. Raise them for fresher results, lower for speed.
- `MAX_TRACKS_PER_ARTIST`: per-artist cap for the main playlist.
- `EMBEDDING_MODEL`: any sentence-transformers model. If you change it, delete the collection, since vector sizes differ.
