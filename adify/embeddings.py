import threading
from typing import Protocol

import numpy as np


class Embedder(Protocol):
    dim: int

    def encode(self, texts: list[str]) -> np.ndarray: ...


class SentenceEmbedder:
    """Lazy wrapper around a sentence-transformers model.

    Loading the model takes a few seconds and ~100MB of RAM, so we only do it
    on first use instead of at import time.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    from sentence_transformers import SentenceTransformer

                    self._model = SentenceTransformer(self.model_name)
        return self._model

    @property
    def dim(self) -> int:
        model = self._load()
        # renamed in newer sentence-transformers versions
        getter = getattr(model, "get_embedding_dimension", None) or model.get_sentence_embedding_dimension
        return getter()

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = self._load().encode(
            texts,
            batch_size=64,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vectors.astype(np.float32)
