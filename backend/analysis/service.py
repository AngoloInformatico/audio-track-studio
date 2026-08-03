"""Streaming silence, energy and spectral boundary analysis."""

import asyncio
import math
import subprocess
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from threading import Event

import numpy as np
from numpy.typing import NDArray

from backend.audio.library import AudioLibrary, AudioLibraryError
from backend.core.config import Settings, get_settings
from backend.models.analysis import AnalysisRequest, AnalysisResult, BoundarySuggestion
from backend.tracks.store import TrackStateNotFoundError, TrackStore

ProgressReporter = Callable[[float, str], None]
FloatArray = NDArray[np.float64]


class AnalysisError(RuntimeError):
    """Raised when automatic analysis cannot complete."""


class _AnalysisCancelled(RuntimeError):
    """Stop a worker thread after its owning asyncio task was cancelled."""


@dataclass(frozen=True, slots=True)
class _Features:
    times: FloatArray
    rms_db: FloatArray
    spectral_centroid: FloatArray
    spectral_flux: FloatArray


class AnalysisService:
    """Extract compact audio features and propose editable boundaries."""

    sample_rate = 11025
    window_seconds = 0.5

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def validate_source(self, audio_id: str) -> None:
        try:
            AudioLibrary.instance().get(audio_id)
            TrackStore.instance().get(audio_id)
        except (AudioLibraryError, TrackStateNotFoundError) as exc:
            raise AnalysisError(str(exc)) from exc

    async def analyze(self, request: AnalysisRequest, report: ProgressReporter) -> dict[str, object]:
        try:
            source = AudioLibrary.instance().get(request.audio_id)
            collection = TrackStore.instance().get(request.audio_id)
        except (AudioLibraryError, TrackStateNotFoundError) as exc:
            raise AnalysisError(str(exc)) from exc
        duration = collection.tracks[-1].end_seconds
        cancel_event = Event()
        worker = asyncio.create_task(
            asyncio.to_thread(
                self._analyze_sync,
                source.path,
                duration,
                request,
                report,
                cancel_event,
            )
        )
        try:
            result = await asyncio.shield(worker)
        except asyncio.CancelledError:
            cancel_event.set()
            with suppress(_AnalysisCancelled, asyncio.CancelledError):
                await asyncio.shield(worker)
            raise
        return result.model_dump()

    def _analyze_sync(
        self,
        source: Path,
        duration: float,
        request: AnalysisRequest,
        report: ProgressReporter,
        cancel_event: Event,
    ) -> AnalysisResult:
        report(1, "Preparazione analisi audio…")
        features = self._extract_features(source, duration, report, cancel_event)
        if cancel_event.is_set():
            raise _AnalysisCancelled
        report(72, "Ricerca dei cambi di brano…")
        suggestions = self._detect_candidates(
            features,
            duration,
            request.sensitivity,
            request.minimum_track_seconds,
        )
        report(96, f"Trovati {len(suggestions)} confini suggeriti")
        return AnalysisResult(
            suggestions=suggestions,
            duration_seconds=duration,
            analyzed_windows=len(features.times),
            sensitivity=request.sensitivity,
            minimum_track_seconds=request.minimum_track_seconds,
        )

    def _extract_features(
        self,
        source: Path,
        duration: float,
        report: ProgressReporter,
        cancel_event: Event,
    ) -> _Features:
        command = [
            self.settings.ffmpeg_binary,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-i",
            str(source),
            "-map",
            "0:a:0",
            "-vn",
            "-ac",
            "1",
            "-ar",
            str(self.sample_rate),
            "-f",
            "f32le",
            "-acodec",
            "pcm_f32le",
            "pipe:1",
        ]
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except FileNotFoundError as exc:
            raise AnalysisError("FFmpeg non è disponibile.") from exc

        window_samples = round(self.sample_rate * self.window_seconds)
        frame_bytes = window_samples * 4
        hann = np.hanning(window_samples)
        frequencies = np.fft.rfftfreq(window_samples, d=1 / self.sample_rate)
        nyquist = self.sample_rate / 2
        times: list[float] = []
        rms_values: list[float] = []
        centroids: list[float] = []
        flux_values: list[float] = []
        previous_spectrum: FloatArray | None = None
        pending = bytearray()
        processed_samples = 0

        try:
            assert process.stdout is not None
            while chunk := process.stdout.read(64 * 1024):
                if cancel_event.is_set():
                    process.terminate()
                    raise _AnalysisCancelled
                pending.extend(chunk)
                while len(pending) >= frame_bytes:
                    raw_frame = bytes(pending[:frame_bytes])
                    del pending[:frame_bytes]
                    samples = np.frombuffer(raw_frame, dtype="<f4").astype(np.float64)
                    rms = math.sqrt(float(np.mean(np.square(samples))))
                    rms_values.append(20 * math.log10(max(rms, 1e-6)))
                    magnitude = np.abs(np.fft.rfft(samples * hann))
                    magnitude_sum = float(np.sum(magnitude))
                    if magnitude_sum > 1e-12:
                        normalized = magnitude / magnitude_sum
                        centroid = float(np.dot(frequencies, normalized) / nyquist)
                    else:
                        normalized = np.zeros_like(magnitude)
                        centroid = 0.0
                    centroids.append(centroid)
                    flux_values.append(
                        0.0
                        if previous_spectrum is None
                        else float(np.sum(np.maximum(normalized - previous_spectrum, 0.0)))
                    )
                    previous_spectrum = normalized
                    processed_samples += window_samples
                    elapsed = processed_samples / self.sample_rate
                    times.append(min(duration, elapsed - self.window_seconds / 2))
                    if len(times) % 8 == 0:
                        progress = min(68.0, elapsed / duration * 68) if duration else 68.0
                        report(progress, f"Analisi spettro: {self._clock(elapsed)} / {self._clock(duration)}")
            return_code = process.wait()
            assert process.stderr is not None
            error_text = process.stderr.read().decode("utf-8", errors="replace").strip()
            if return_code != 0:
                raise AnalysisError(error_text or "FFmpeg non ha completato la decodifica audio.")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()

        return _Features(
            times=np.asarray(times, dtype=np.float64),
            rms_db=np.asarray(rms_values, dtype=np.float64),
            spectral_centroid=np.asarray(centroids, dtype=np.float64),
            spectral_flux=np.asarray(flux_values, dtype=np.float64),
        )

    def _detect_candidates(
        self,
        features: _Features,
        duration: float,
        sensitivity: int,
        minimum_track_seconds: float,
    ) -> list[BoundarySuggestion]:
        if len(features.times) < 3:
            return []
        silence_threshold = -50.0 + sensitivity * 0.16
        quiet = features.rms_db <= silence_threshold
        candidates: list[BoundarySuggestion] = []
        minimum_quiet_windows = 3 if sensitivity < 35 else 2 if sensitivity < 75 else 1
        start: int | None = None
        for index, is_quiet in enumerate(np.append(quiet, False)):
            if is_quiet and start is None:
                start = index
            elif not is_quiet and start is not None:
                end = index - 1
                if end - start + 1 >= minimum_quiet_windows:
                    quietest = start + int(np.argmin(features.rms_db[start : end + 1]))
                    timestamp = float((features.times[start] + features.times[end]) / 2)
                    depth = max(0.0, silence_threshold - float(features.rms_db[quietest]))
                    confidence = min(0.98, 0.58 + depth / 45 + (end - start) * 0.035)
                    candidates.append(
                        BoundarySuggestion(
                            timestamp_seconds=round(timestamp, 3),
                            confidence=round(confidence, 3),
                            signals=["silenzio/calo di volume"],
                        )
                    )
                start = None

        energy_jump = np.abs(np.diff(features.rms_db, prepend=features.rms_db[0]))
        centroid_jump = np.abs(
            np.diff(features.spectral_centroid, prepend=features.spectral_centroid[0])
        )
        energy_score = self._robust_score(energy_jump)
        flux_score = self._robust_score(features.spectral_flux)
        centroid_score = self._robust_score(centroid_jump)
        novelty = energy_score * 0.42 + flux_score * 0.36 + centroid_score * 0.22
        novelty_threshold = 0.72 - sensitivity * 0.0034
        for index in range(1, len(novelty) - 1):
            score = float(novelty[index])
            if score < novelty_threshold or score < novelty[index - 1] or score < novelty[index + 1]:
                continue
            signals: list[str] = []
            if energy_score[index] >= 0.45:
                signals.append("variazione energetica")
            if flux_score[index] >= 0.45:
                signals.append("cambiamento spettrale")
            if centroid_score[index] >= 0.45:
                signals.append("variazione timbrica")
            candidates.append(
                BoundarySuggestion(
                    timestamp_seconds=round(float(features.times[index]), 3),
                    confidence=round(min(0.96, 0.48 + score * 0.5), 3),
                    signals=signals or ["novelty audio"],
                )
            )

        eligible = [
            candidate
            for candidate in candidates
            if minimum_track_seconds <= candidate.timestamp_seconds <= duration - minimum_track_seconds
        ]
        return self._merge_nearby(eligible, minimum_track_seconds)

    @staticmethod
    def _robust_score(values: FloatArray) -> FloatArray:
        median = float(np.median(values))
        deviation = float(np.median(np.abs(values - median)))
        scale = max(1e-9, 1.4826 * deviation)
        z_score = np.maximum(0.0, (values - median) / scale)
        return np.clip((z_score - 0.8) / 5.0, 0.0, 1.0)

    @staticmethod
    def _merge_nearby(
        candidates: list[BoundarySuggestion], minimum_gap: float
    ) -> list[BoundarySuggestion]:
        selected: list[BoundarySuggestion] = []
        for candidate in sorted(candidates, key=lambda item: item.timestamp_seconds):
            if selected and candidate.timestamp_seconds - selected[-1].timestamp_seconds < minimum_gap:
                current = selected[-1]
                if candidate.confidence > current.confidence:
                    merged_signals = list(dict.fromkeys([*current.signals, *candidate.signals]))
                    selected[-1] = candidate.model_copy(update={"signals": merged_signals})
                else:
                    current.signals = list(dict.fromkeys([*current.signals, *candidate.signals]))
                continue
            selected.append(candidate)
        return selected

    @staticmethod
    def _clock(seconds: float) -> str:
        total = max(0, round(seconds))
        return f"{total // 60:02d}:{total % 60:02d}"
