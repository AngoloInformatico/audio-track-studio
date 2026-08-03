"""Automatic boundary analysis request and result models."""

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    audio_id: str = Field(min_length=1, max_length=100)
    sensitivity: int = Field(default=55, ge=0, le=100)
    minimum_track_seconds: float = Field(default=20.0, ge=5.0, le=300.0)


class AnalysisConfig(BaseModel):
    default_sensitivity: int = 55
    default_minimum_track_seconds: float = 20.0
    sample_rate: int = 11025
    window_seconds: float = 0.5
    method_note: str = (
        "Combina silenzi e cali di volume con variazioni energetiche e spettrali. "
        "I risultati sono suggerimenti modificabili."
    )


class BoundarySuggestion(BaseModel):
    timestamp_seconds: float = Field(gt=0)
    confidence: float = Field(ge=0, le=1)
    signals: list[str]


class AnalysisResult(BaseModel):
    suggestions: list[BoundarySuggestion]
    duration_seconds: float = Field(gt=0)
    analyzed_windows: int = Field(ge=0)
    sensitivity: int = Field(ge=0, le=100)
    minimum_track_seconds: float = Field(ge=5)
    method: str = "silence_energy_spectral"
