"""Music recognition request, readiness and result models."""

from typing import Literal

from pydantic import BaseModel, Field


class RecognitionRequest(BaseModel):
    audio_id: str = Field(min_length=1, max_length=100)
    track_ids: list[str] | None = Field(default=None, max_length=999)
    max_candidates: int = Field(default=3, ge=1, le=5)


class RecognitionConfig(BaseModel):
    provider: str = "acoustid"
    available: bool
    fpcalc_available: bool
    fpcalc_version: str | None = None
    api_key_configured: bool
    online_required: bool = True
    maximum_sample_seconds: int = 120
    message: str


class AcoustIDSetupUpdate(BaseModel):
    acoustid_api_key: str | None = Field(default=None, min_length=1, max_length=200)
    fpcalc_path: str | None = Field(default=None, min_length=1, max_length=1000)


class AcoustIDSetupStatus(BaseModel):
    available: bool
    api_key_configured: bool
    fpcalc_available: bool
    fpcalc_version: str | None = None
    fpcalc_path: str
    fpcalc_managed: bool
    chromaprint_version: str
    message: str


class RecognitionCandidate(BaseModel):
    artist: str
    title: str
    album: str | None = None
    date: str | None = None
    confidence: float = Field(ge=0, le=1)
    provider: str = "acoustid"
    external_id: str | None = None
    recording_id: str | None = None
    release_group_id: str | None = None


class TrackRecognition(BaseModel):
    track_id: str
    track_number: int = Field(ge=1)
    status: Literal["matched", "unmatched", "error"]
    candidates: list[RecognitionCandidate] = Field(default_factory=list)
    error: str | None = None


class RecognitionResult(BaseModel):
    provider: str
    tracks: list[TrackRecognition]
    matched_count: int = Field(ge=0)
    unmatched_count: int = Field(ge=0)
    error_count: int = Field(ge=0)


class RecognitionMetadataItem(BaseModel):
    track_id: str = Field(min_length=1, max_length=100)
    artist: str = Field(max_length=300)
    title: str = Field(max_length=300)
    album: str | None = Field(default=None, max_length=300)
    date: str | None = Field(default=None, max_length=32)
    release_group_id: str | None = Field(default=None, max_length=36)
    provider: str | None = Field(default=None, max_length=50)
    external_id: str | None = Field(default=None, max_length=100)
    recording_id: str | None = Field(default=None, max_length=100)
    confidence: float | None = Field(default=None, ge=0, le=1)


class RecognitionMetadataApply(BaseModel):
    items: list[RecognitionMetadataItem] = Field(min_length=1, max_length=999)
