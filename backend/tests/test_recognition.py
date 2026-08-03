import asyncio
from pathlib import Path

from backend.audio.library import AudioLibrary, ImportedAudio
from backend.core.config import Settings
from backend.models.recognition import RecognitionCandidate, RecognitionConfig, RecognitionRequest
from backend.recognition.acoustid import AcoustIDProvider
from backend.recognition.base import MusicRecognitionProvider
from backend.recognition.service import RecognitionService
from backend.tracks.store import TrackStore


def test_acoustid_parser_returns_ranked_unique_candidates() -> None:
    payload = {
        "results": [
            {
                "id": "match-1",
                "score": 0.92,
                "recordings": [
                    {
                        "id": "recording-1",
                        "title": "Example Song",
                        "artists": [{"name": "Example Artist"}],
                        "releasegroups": [
                            {
                                "id": "48140466-cff6-3222-bd55-63c27e43190d",
                                "title": "Example Album",
                            }
                        ],
                    },
                    {
                        "id": "recording-1",
                        "title": "Example Song",
                        "artists": [{"name": "Example Artist"}],
                    },
                ],
            }
        ]
    }

    candidates = AcoustIDProvider.parse_candidates(payload, 3)

    assert len(candidates) == 1
    assert candidates[0].artist == "Example Artist"
    assert candidates[0].title == "Example Song"
    assert candidates[0].album == "Example Album"
    assert candidates[0].confidence == 0.92
    assert candidates[0].recording_id == "recording-1"
    assert candidates[0].release_group_id == "48140466-cff6-3222-bd55-63c27e43190d"


def test_readiness_does_not_expose_api_key(monkeypatch) -> None:
    secret = "private-test-key"
    provider = AcoustIDProvider(Settings(acoustid_api_key=secret))

    async def unavailable() -> None:
        return None

    monkeypatch.setattr(provider, "_inspect_fpcalc", unavailable)
    readiness = asyncio.run(provider.inspect())

    assert readiness.available is False
    assert readiness.api_key_configured is True
    assert secret not in readiness.model_dump_json()


def test_sample_windows_avoid_boundaries_and_offer_fallbacks() -> None:
    short = AcoustIDProvider.sample_windows(10.0, 70.0)
    long = AcoustIDProvider.sample_windows(10.0, 410.0)

    assert short == [(15.0, 50.0)]
    assert len(long) == 3
    assert long[0] == (150.0, 120.0)
    assert long[1] == (15.0, 120.0)
    assert long[2] == (285.0, 120.0)


def test_service_recognizes_selected_tracks_and_reports_progress(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "source.wav"
    source.touch()
    audio_id = "recognition-audio"
    store = TrackStore.instance()
    store.initialize(audio_id, 40.0)
    collection = store.replace_markers(audio_id, [20.0])
    imported = ImportedAudio(audio_id, source, source.name, "audio/wav")
    monkeypatch.setattr(AudioLibrary.instance(), "get", lambda _: imported)
    provider = _FakeProvider()
    progress: list[tuple[float, str]] = []
    request = RecognitionRequest(
        audio_id=audio_id,
        track_ids=[track.id for track in collection.tracks],
        max_candidates=2,
    )
    try:
        result = asyncio.run(
            RecognitionService(provider).recognize(
                request,
                lambda percent, message: progress.append((percent, message)),
            )
        )
    finally:
        store.remove(audio_id)

    assert result["matched_count"] == 2
    assert result["error_count"] == 0
    assert len(result["tracks"]) == 2
    assert len(progress) == 2
    assert provider.calls == [(0.0, 20.0), (20.0, 40.0)]


class _FakeProvider(MusicRecognitionProvider):
    name = "fake"

    def __init__(self) -> None:
        self.calls: list[tuple[float, float]] = []

    async def inspect(self) -> RecognitionConfig:
        return RecognitionConfig(
            available=True,
            fpcalc_available=True,
            api_key_configured=True,
            message="ready",
        )

    async def recognize(
        self,
        source: Path,
        start_seconds: float,
        end_seconds: float,
        max_candidates: int,
    ) -> list[RecognitionCandidate]:
        self.calls.append((start_seconds, end_seconds))
        return [
            RecognitionCandidate(
                artist=f"Artist {len(self.calls)}",
                title=f"Title {len(self.calls)}",
                confidence=0.9,
                provider=self.name,
            )
        ][:max_candidates]
