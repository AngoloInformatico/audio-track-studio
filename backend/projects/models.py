"""Portable .atsproject document and API models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ProjectSource(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    size_bytes: int = Field(gt=0)
    duration_seconds: float = Field(gt=0)
    format: str = Field(min_length=1, max_length=20)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ProjectCover(BaseModel):
    mime_type: Literal["image/jpeg", "image/png"]
    source: Literal["manual", "cover_art_archive", "source"]
    data_base64: str = Field(min_length=4)


class ProjectTrack(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    number: int = Field(ge=1)
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    artist: str = Field(default="", max_length=300)
    title: str = Field(default="", max_length=300)
    album: str = Field(default="", max_length=300)
    album_artist: str = Field(default="", max_length=300)
    track_number: int | None = Field(default=None, ge=1, le=9999)
    disc_number: int | None = Field(default=None, ge=1, le=999)
    date: str = Field(default="", max_length=32)
    genre: str = Field(default="", max_length=150)
    comment: str = Field(default="", max_length=2000)
    composer: str = Field(default="", max_length=300)
    release_group_id: str | None = Field(default=None, max_length=36)
    recognition_provider: str | None = Field(default=None, max_length=50)
    recognition_external_id: str | None = Field(default=None, max_length=100)
    recognition_recording_id: str | None = Field(default=None, max_length=100)
    recognition_confidence: float | None = Field(default=None, ge=0, le=1)
    cover_key: str | None = None


class ProjectSettings(BaseModel):
    theme: Literal["light", "dark", "system"] = "system"
    autosave_enabled: bool = False


class ProjectDocument(BaseModel):
    schema_name: Literal["audio-track-studio-project"] = "audio-track-studio-project"
    schema_version: Literal[1] = 1
    id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    created_at: datetime
    updated_at: datetime
    source: ProjectSource
    markers: list[float] = Field(max_length=999)
    tracks: list[ProjectTrack] = Field(min_length=1, max_length=1000)
    covers: dict[str, ProjectCover] = Field(default_factory=dict)
    settings: ProjectSettings = Field(default_factory=ProjectSettings)


class ProjectSummary(BaseModel):
    id: str
    name: str
    source_name: str
    created_at: datetime
    updated_at: datetime
    track_count: int = Field(ge=1)
    has_covers: bool
    kind: Literal["saved", "recovery"] = "saved"
    download_url: str | None = None


class ProjectSaveRequest(BaseModel):
    audio_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    project_id: str | None = Field(default=None, max_length=100)
    save_as: bool = False
    settings: ProjectSettings = Field(default_factory=ProjectSettings)


class ProjectSaveResult(BaseModel):
    project: ProjectSummary
    path: str


class ProjectAutosaveRequest(BaseModel):
    audio_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    project_id: str | None = Field(default=None, max_length=100)
    settings: ProjectSettings = Field(default_factory=ProjectSettings)


class ProjectPrepareRequest(BaseModel):
    project_id: str | None = Field(default=None, max_length=100)
    recovery_id: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def exactly_one_source(self) -> "ProjectPrepareRequest":
        if bool(self.project_id) == bool(self.recovery_id):
            raise ValueError("Indica un solo progetto salvato o recovery.")
        return self


class ProjectPreview(BaseModel):
    token: str
    name: str
    source: ProjectSource
    track_count: int
    has_covers: bool
    settings: ProjectSettings
    persisted_project_id: str | None = None


class ProjectApplyRequest(BaseModel):
    token: str = Field(min_length=1, max_length=100)
    audio_id: str = Field(min_length=1, max_length=100)


class ProjectApplyResult(BaseModel):
    project: ProjectSummary
    persisted_project_id: str | None = None
    markers: list[float]
    track_count: int
