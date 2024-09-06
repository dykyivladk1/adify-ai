from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Track:
    id: str
    name: str
    artists: list[str]
    artist_ids: list[str]
    album: str = ""
    release_year: int | None = None
    genres: list[str] = field(default_factory=list)
    # search phrases that surfaced this track - cheap but useful context,
    # e.g. a track found via genre:"lo-fi" + "study" gets those words attached
    tags: list[str] = field(default_factory=list)
    explicit: bool = False

    @property
    def uri(self) -> str:
        return f"spotify:track:{self.id}"

    @property
    def url(self) -> str:
        return f"https://open.spotify.com/track/{self.id}"

    @property
    def main_artist_id(self) -> str:
        return self.artist_ids[0] if self.artist_ids else ""

    def document(self) -> str:
        """Text we embed. Keep it short, the model truncates at 256 tokens anyway."""
        parts = [f"{self.name} by {', '.join(self.artists)}"]
        if self.album and self.album != self.name:
            parts.append(f"from the album {self.album}")
        if self.release_year:
            parts.append(f"released {self.release_year}")
        if self.genres:
            parts.append(f"genres: {', '.join(self.genres[:6])}")
        if self.tags:
            parts.append(f"vibe: {', '.join(self.tags[:8])}")
        return ". ".join(parts)

    def to_payload(self) -> dict:
        return asdict(self)

    @classmethod
    def from_payload(cls, payload: dict) -> "Track":
        known = {k: payload[k] for k in cls.__dataclass_fields__ if k in payload}
        return cls(**known)
