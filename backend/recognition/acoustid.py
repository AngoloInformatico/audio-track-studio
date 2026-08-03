"""Chromaprint/fpcalc fingerprinting with AcoustID lookup."""

import asyncio
import json
import shutil
import subprocess
from pathlib import Path
from threading import Lock
from time import monotonic, sleep
from typing import Any
from uuid import uuid4

import httpx

from backend.core.config import Settings, get_settings
from backend.models.recognition import RecognitionCandidate, RecognitionConfig
from backend.recognition.base import (
    MusicRecognitionProvider,
    RecognitionProviderError,
    RecognitionProviderUnavailable,
)


class AcoustIDProvider(MusicRecognitionProvider):
    """Generate a compact Chromaprint fingerprint and query AcoustID."""

    name = "acoustid"
    maximum_sample_seconds = 120.0
    minimum_sample_seconds = 6.0
    _rate_lock = Lock()
    _last_lookup_at = 0.0

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def inspect(self) -> RecognitionConfig:
        version = await self._inspect_fpcalc()
        fpcalc_available = version is not None
        key_configured = bool(self.settings.acoustid_api_key)
        if not fpcalc_available:
            message = "Chromaprint/fpcalc non è disponibile. Configura ATS_FPCALC_BINARY."
        elif not key_configured:
            message = "Configura ACOUSTID_API_KEY per abilitare il riconoscimento online."
        else:
            message = "Provider AcoustID pronto. I risultati dovranno essere confermati manualmente."
        return RecognitionConfig(
            available=fpcalc_available and key_configured,
            fpcalc_available=fpcalc_available,
            fpcalc_version=version,
            api_key_configured=key_configured,
            maximum_sample_seconds=round(self.maximum_sample_seconds),
            message=message,
        )

    async def recognize(
        self,
        source: Path,
        start_seconds: float,
        end_seconds: float,
        max_candidates: int,
    ) -> list[RecognitionCandidate]:
        readiness = await self.inspect()
        if not readiness.available:
            raise RecognitionProviderUnavailable(readiness.message)
        segment_duration = end_seconds - start_seconds
        if segment_duration < self.minimum_sample_seconds:
            raise RecognitionProviderError("La traccia è troppo breve per un fingerprint affidabile.")
        temporary = source.parent / f".recognition-{uuid4().hex}.wav"
        try:
            for sample_start, sample_duration in self.sample_windows(start_seconds, end_seconds):
                await self._extract_sample(source, temporary, sample_start, sample_duration)
                duration, fingerprint = await self._fingerprint(temporary, sample_duration)
                payload = await self._lookup(duration, fingerprint)
                candidates = self.parse_candidates(payload, max_candidates)
                if candidates:
                    return candidates
            return []
        finally:
            await asyncio.to_thread(temporary.unlink, missing_ok=True)

    @classmethod
    def sample_windows(cls, start_seconds: float, end_seconds: float) -> list[tuple[float, float]]:
        """Prefer the interior, then try initial/final windows after an empty lookup."""

        duration = end_seconds - start_seconds
        edge_guard = min(5.0, max(0.0, (duration - cls.minimum_sample_seconds) / 4))
        usable_start = start_seconds + edge_guard
        usable_end = end_seconds - edge_guard
        usable_duration = usable_end - usable_start
        if usable_duration <= cls.maximum_sample_seconds:
            return [(usable_start, usable_duration)]

        length = cls.maximum_sample_seconds
        starts = [
            usable_start + (usable_duration - length) / 2,
            usable_start,
            usable_end - length,
        ]
        windows: list[tuple[float, float]] = []
        for candidate in starts:
            if not any(abs(candidate - existing) < 1.0 for existing, _ in windows):
                windows.append((candidate, length))
        return windows

    async def _extract_sample(
        self,
        source: Path,
        destination: Path,
        start_seconds: float,
        duration: float,
    ) -> None:
        command = [
            self.settings.ffmpeg_binary,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-ss",
            f"{start_seconds:.3f}",
            "-i",
            str(source),
            "-t",
            f"{duration:.3f}",
            "-map",
            "0:a:0",
            "-vn",
            "-ac",
            "2",
            "-ar",
            "44100",
            "-c:a",
            "pcm_s16le",
            "-y",
            str(destination),
        ]
        try:
            result = await self._run(command, self.settings.recognition_timeout_seconds)
        except FileNotFoundError as exc:
            raise RecognitionProviderUnavailable("FFmpeg non è disponibile.") from exc
        if result.returncode != 0:
            raise RecognitionProviderError(
                result.stderr.strip() or "FFmpeg non ha preparato il campione audio."
            )

    async def _fingerprint(self, path: Path, maximum_length: float) -> tuple[int, str]:
        command = [
            self.settings.fpcalc_binary,
            "-json",
            "-length",
            f"{maximum_length:.3f}",
            str(path),
        ]
        try:
            result = await self._run(command, self.settings.recognition_timeout_seconds)
        except FileNotFoundError as exc:
            raise RecognitionProviderUnavailable("Chromaprint/fpcalc non è disponibile.") from exc
        if result.returncode != 0:
            raise RecognitionProviderError(
                result.stderr.strip() or "fpcalc non ha generato il fingerprint."
            )
        try:
            payload = json.loads(result.stdout)
            duration = max(1, round(float(payload["duration"])))
            fingerprint = str(payload["fingerprint"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RecognitionProviderError("fpcalc ha restituito dati non validi.") from exc
        if not fingerprint:
            raise RecognitionProviderError("fpcalc ha restituito un fingerprint vuoto.")
        return duration, fingerprint

    async def _lookup(self, duration: int, fingerprint: str) -> dict[str, Any]:
        await asyncio.to_thread(self._wait_for_rate_slot)
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.recognition_timeout_seconds,
                headers={"User-Agent": "AudioTrackStudio/0.5"},
            ) as client:
                response = await client.post(
                    self.settings.acoustid_lookup_url,
                    data={
                        "client": self.settings.acoustid_api_key,
                        "duration": str(duration),
                        "fingerprint": fingerprint,
                        "meta": "recordings releases releasegroups compress",
                        "format": "json",
                    },
                )
            response.raise_for_status()
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            raise RecognitionProviderUnavailable(
                "Riconoscimento online non disponibile. Puoi continuare manualmente."
            ) from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise RecognitionProviderError("AcoustID ha restituito una risposta non valida.") from exc
        if payload.get("status") != "ok":
            detail = payload.get("error") or {}
            message = detail.get("message") if isinstance(detail, dict) else None
            raise RecognitionProviderError(message or "AcoustID non ha completato la ricerca.")
        return payload

    @classmethod
    def _wait_for_rate_slot(cls) -> None:
        with cls._rate_lock:
            delay = 0.34 - (monotonic() - cls._last_lookup_at)
            if delay > 0:
                sleep(delay)
            cls._last_lookup_at = monotonic()

    async def _inspect_fpcalc(self) -> str | None:
        binary = self.settings.fpcalc_binary
        if not Path(binary).is_file() and shutil.which(binary) is None:
            return None
        try:
            result = await self._run([binary, "-version"], 5)
        except (FileNotFoundError, RecognitionProviderError):
            return None
        if result.returncode != 0:
            return None
        return result.stdout.splitlines()[0] if result.stdout else "fpcalc"

    @staticmethod
    async def _run(command: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except FileNotFoundError:
            raise
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except TimeoutError as exc:
            process.kill()
            await process.wait()
            raise RecognitionProviderError("Uno strumento di riconoscimento non ha risposto.") from exc
        except asyncio.CancelledError:
            if process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5)
                except TimeoutError:
                    process.kill()
                    await process.wait()
            raise
        return subprocess.CompletedProcess(
            command,
            process.returncode,
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
        )

    @staticmethod
    def parse_candidates(payload: dict[str, Any], limit: int) -> list[RecognitionCandidate]:
        candidates: list[RecognitionCandidate] = []
        seen: set[tuple[str, str, str | None]] = set()
        for result in payload.get("results") or []:
            try:
                score = min(1.0, max(0.0, float(result.get("score") or 0.0)))
            except (TypeError, ValueError):
                continue
            acoustid = result.get("id")
            for recording in result.get("recordings") or []:
                title = str(recording.get("title") or "").strip()
                artists = recording.get("artists") or []
                artist = ", ".join(
                    str(item.get("name") or "").strip() for item in artists if item.get("name")
                )
                if not title or not artist:
                    continue
                releasegroups = recording.get("releasegroups") or []
                releases = recording.get("releases") or []
                album = next(
                    (
                        str(item.get("title")).strip()
                        for item in [*releases, *releasegroups]
                        if item.get("title")
                    ),
                    None,
                )
                date = next(
                    (str(item.get("date")).strip() for item in releases if item.get("date")),
                    None,
                )
                recording_id = recording.get("id")
                release_group_id = next(
                    (str(item.get("id")) for item in releasegroups if item.get("id")),
                    None,
                )
                key = (artist.casefold(), title.casefold(), recording_id)
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(
                    RecognitionCandidate(
                        artist=artist,
                        title=title,
                        album=album,
                        date=date,
                        confidence=round(score, 4),
                        external_id=str(acoustid) if acoustid else None,
                        recording_id=str(recording_id) if recording_id else None,
                        release_group_id=release_group_id,
                    )
                )
        candidates.sort(key=lambda item: item.confidence, reverse=True)
        return candidates[:limit]
