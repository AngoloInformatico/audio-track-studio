"""Provider contract for music recognition."""

from abc import ABC, abstractmethod
from pathlib import Path

from backend.models.recognition import RecognitionCandidate, RecognitionConfig


class RecognitionProviderError(RuntimeError):
    """Raised when a provider cannot fingerprint or identify a sample."""


class RecognitionProviderUnavailable(RecognitionProviderError):
    """Raised when a provider dependency or its remote service is unavailable."""


class MusicRecognitionProvider(ABC):
    """Isolate fingerprinting and lookup from application orchestration."""

    name: str

    @abstractmethod
    async def inspect(self) -> RecognitionConfig:
        """Return readiness without exposing secrets."""

    @abstractmethod
    async def recognize(
        self,
        source: Path,
        start_seconds: float,
        end_seconds: float,
        max_candidates: int,
    ) -> list[RecognitionCandidate]:
        """Recognize a bounded segment and return ranked candidates."""
