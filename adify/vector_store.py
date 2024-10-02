from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from .embeddings import Embedder
from .models import Track

log = logging.getLogger(__name__)

# Qdrant wants UUIDs or ints as point ids, Spotify ids are base62 strings.
_NAMESPACE = uuid.UUID("5f1b3a52-6b0e-4c9a-9a57-3e0a3e2f9d11")


def point_id(track_id: str) -> str:
    return str(uuid.uuid5(_NAMESPACE, track_id))


@dataclass
class Hit:
    track: Track
    score: float
    vector: np.ndarray


class TrackStore:
    def __init__(self, client: QdrantClient, collection: str, embedder: Embedder, remote: bool = False):
        self.client = client
        self.collection = collection
        self.embedder = embedder
        self.remote = remote
        self._ready = False

    @classmethod
    def from_settings(cls, settings, embedder: Embedder) -> "TrackStore":
        if settings.qdrant_url:
            client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
            return cls(client, settings.collection, embedder, remote=True)

        log.info("QDRANT_URL not set, using embedded Qdrant at %s", settings.qdrant_path)
        return cls(QdrantClient(path=settings.qdrant_path), settings.collection, embedder)

    def ensure_collection(self) -> None:
        if self._ready:
            return
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                self.collection,
                vectors_config=qm.VectorParams(size=self.embedder.dim, distance=qm.Distance.COSINE),
            )
            if self.remote:  # embedded mode doesn't support payload indexes
                self.client.create_payload_index(self.collection, "explicit", qm.PayloadSchemaType.BOOL)
        self._ready = True

    def count(self) -> int:
        self.ensure_collection()
        return self.client.count(self.collection, exact=False).count

    def upsert(self, tracks: list[Track]) -> int:
        if not tracks:
            return 0
        self.ensure_collection()

        # Merge with what's already stored so tags/genres accumulate over time
        # instead of being overwritten by whichever query saw the track last.
        existing = {
            p.payload["id"]: Track.from_payload(p.payload)
            for p in self.client.retrieve(self.collection, ids=[point_id(t.id) for t in tracks], with_payload=True)
        }
        merged = []
        for track in tracks:
            old = existing.get(track.id)
            if old:
                track.tags = _union(old.tags, track.tags)
                track.genres = _union(old.genres, track.genres)
            merged.append(track)

        vectors = self.embedder.encode([t.document() for t in merged])
        self.client.upsert(
            self.collection,
            points=[
                qm.PointStruct(id=point_id(t.id), vector=v.tolist(), payload=t.to_payload())
                for t, v in zip(merged, vectors)
            ],
        )
        return len(merged)

    def search(self, vector: np.ndarray, limit: int = 200, exclude_explicit: bool = False) -> list[Hit]:
        self.ensure_collection()
        query_filter = None
        if exclude_explicit:
            query_filter = qm.Filter(
                must_not=[qm.FieldCondition(key="explicit", match=qm.MatchValue(value=True))]
            )
        result = self.client.query_points(
            self.collection,
            query=vector.tolist(),
            limit=limit,
            query_filter=query_filter,
            with_payload=True,
            with_vectors=True,
        )
        return [
            Hit(Track.from_payload(p.payload), p.score, np.asarray(p.vector, dtype=np.float32))
            for p in result.points
        ]


def _union(a: list[str], b: list[str]) -> list[str]:
    seen = dict.fromkeys(a)
    seen.update(dict.fromkeys(b))
    return list(seen)
