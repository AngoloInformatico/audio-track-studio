"""Recognition orchestration across one or many editor tracks."""

import asyncio
from collections.abc import Callable

from backend.audio.library import AudioLibrary, AudioLibraryError
from backend.models.recognition import (
    RecognitionRequest,
    RecognitionResult,
    TrackRecognition,
)
from backend.recognition.base import (
    MusicRecognitionProvider,
    RecognitionProviderError,
    RecognitionProviderUnavailable,
)
from backend.tracks.store import TrackStateNotFoundError, TrackStore

ProgressReporter = Callable[[float, str], None]


class RecognitionError(RuntimeError):
    """Raised when a recognition request is invalid."""


class RecognitionService:
    """Run a provider sequentially so progress and rate limits remain predictable."""

    def __init__(self, provider: MusicRecognitionProvider) -> None:
        self.provider = provider

    def validate_request(self, request: RecognitionRequest) -> None:
        try:
            AudioLibrary.instance().get(request.audio_id)
            collection = TrackStore.instance().get(request.audio_id)
        except (AudioLibraryError, TrackStateNotFoundError) as exc:
            raise RecognitionError(str(exc)) from exc
        if request.track_ids:
            available = {track.id for track in collection.tracks}
            unknown = next((track_id for track_id in request.track_ids if track_id not in available), None)
            if unknown:
                raise RecognitionError("Una traccia richiesta non esiste più.")

    async def recognize(self, request: RecognitionRequest, report: ProgressReporter) -> dict[str, object]:
        source = AudioLibrary.instance().get(request.audio_id)
        collection = TrackStore.instance().get(request.audio_id)
        selected_ids = set(request.track_ids) if request.track_ids else None
        tracks = [track for track in collection.tracks if selected_ids is None or track.id in selected_ids]
        results: list[TrackRecognition] = []
        total = len(tracks)
        for index, track in enumerate(tracks, start=1):
            report((index - 1) / total * 96, f"Riconoscimento traccia {index} di {total}")
            try:
                candidates = await self.provider.recognize(
                    source.path,
                    track.start_seconds,
                    track.end_seconds,
                    request.max_candidates,
                )
                results.append(
                    TrackRecognition(
                        track_id=track.id,
                        track_number=track.number,
                        status="matched" if candidates else "unmatched",
                        candidates=candidates,
                    )
                )
            except asyncio.CancelledError:
                raise
            except RecognitionProviderUnavailable as exc:
                message = str(exc)
                results.append(
                    TrackRecognition(
                        track_id=track.id,
                        track_number=track.number,
                        status="error",
                        error=message,
                    )
                )
                results.extend(
                    TrackRecognition(
                        track_id=remaining.id,
                        track_number=remaining.number,
                        status="error",
                        error=message,
                    )
                    for remaining in tracks[index:]
                )
                break
            except RecognitionProviderError as exc:
                results.append(
                    TrackRecognition(
                        track_id=track.id,
                        track_number=track.number,
                        status="error",
                        error=str(exc),
                    )
                )
        matched = sum(item.status == "matched" for item in results)
        unmatched = sum(item.status == "unmatched" for item in results)
        errors = sum(item.status == "error" for item in results)
        return RecognitionResult(
            provider=self.provider.name,
            tracks=results,
            matched_count=matched,
            unmatched_count=unmatched,
            error_count=errors,
        ).model_dump()
