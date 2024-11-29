import hashlib
import os
import re

import numpy as np
import pytest
from qdrant_client import QdrantClient

# settings are read at import time, so set fake creds before importing adify
os.environ.setdefault("SPOTIFY_CLIENT_ID", "test-id")
os.environ.setdefault("SPOTIFY_CLIENT_SECRET", "test-secret")

from adify.models import Track  # noqa: E402
from adify.vector_store import TrackStore  # noqa: E402


class HashEmbedder:
    """Bag-of-words hashing embedder. Dumb, but deterministic and it means
    tests don't download a 90MB model."""

    dim = 256

    def encode(self, texts):
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            for word in re.findall(r"[a-z0-9&-]+", text.lower()):
                idx = int(hashlib.md5(word.encode()).hexdigest(), 16) % self.dim
                out[row, idx] += 1.0
            norm = np.linalg.norm(out[row])
            if norm:
                out[row] /= norm
        return out


