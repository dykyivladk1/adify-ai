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


