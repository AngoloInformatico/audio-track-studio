"""Track boundaries, editable metadata, and cover API models."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CoverInfo(BaseModel):
    url: str
    mime_type: Literal["image/jpeg", "image/png"]
    size_bytes: int = Field(gt=0)
    source: Literal["manual", "cover_art_archive", "source"]


class Track(BaseModel):
    id: str
    number: int = Field(ge=1)
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    artist: str = ""
    title: str = ""
    album: str = ""
    album_artist: str = ""
    track_number: int | None = Field(default=None, ge=1, le=9999)
    disc_number: int | None = Field(default=None, ge=1, le=999)
    date: str = ""
    genre: str = ""
    comment: str = ""
    composer: str = ""
    release_group_id: str | None = None
    recognition_provider: str | None = None
    recognition_external_id: str | None = None
    recognition_recording_id: str | None = None
    recognition_confidence: float | None = Field(default=None, ge=0, le=1)
    cover: CoverInfo | None = None


class TrackCollection(BaseModel):
    markers: list[float]
    tracks: list[Track]


class MarkerUpdate(BaseModel):
    markers: list[float] = Field(max_length=999)


class TrackMetadataUpdate(BaseModel):
    artist: str | None = Field(default=None, max_length=300)
    title: str | None = Field(default=None, max_length=300)
    album: str | None = Field(default=None, max_length=300)
    album_artist: str | None = Field(default=None, max_length=300)
    track_number: int | None = Field(default=None, ge=1, le=9999)
    disc_number: int | None = Field(default=None, ge=1, le=999)
    date: str | None = Field(default=None, max_length=32)
    genre: str | None = Field(default=None, max_length=150)
    comment: str | None = Field(default=None, max_length=2000)
    composer: str | None = Field(default=None, max_length=300)

    @field_validator(
        "artist",
        "title",
        "album",
        "album_artist",
        "date",
        "genre",
        "comment",
        "composer",
    )
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class CoverArtArchiveRequest(BaseModel):
    release_group_id: str = Field(pattern=r"^[0-9a-fA-F-]{36}$")
