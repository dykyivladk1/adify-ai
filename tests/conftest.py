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


