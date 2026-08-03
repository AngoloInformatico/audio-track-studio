"""Audio API response models."""

from pydantic import BaseModel, Field


class AudioInfo(BaseModel):
    name: str
    format: str
    codec: str | None = None
    duration_seconds: float = Field(ge=0)
    sample_rate: int | None = Field(default=None, gt=0)
    bit_depth: int | None = Field(default=None, gt=0)
    channels: int | None = Field(default=None, gt=0)
    channel_layout: str | None = None
    bitrate: int | None = Field(default=None, gt=0)
    size_bytes: int = Field(ge=0)


class AudioSession(BaseModel):
    id: str
    info: AudioInfo
    stream_url: str
