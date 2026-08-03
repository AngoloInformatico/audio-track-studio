"""Export request and configuration models."""

from typing import Literal

from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    audio_id: str = Field(min_length=1, max_length=100)
    destination: str = Field(min_length=1, max_length=2048)
    format: Literal["flac"] = "flac"
    filename_template: str = Field(
        default="{track:02d} - {artist} - {title}.flac", min_length=1, max_length=300
    )
    overwrite: bool = False
    embed_metadata: bool = True
    embed_cover: bool = True
    save_cover_file: bool = False
    compression_level: int = Field(default=8, ge=0, le=12)


class ExportConfig(BaseModel):
    default_directory: str
    default_template: str = "{track:02d} - {artist} - {title}.flac"
    formats: list[str] = Field(default_factory=lambda: ["flac"])
    mode_note: str = "Ricodifica FLAC lossless per garantire tagli precisi."
