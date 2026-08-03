"""Precise FLAC splitting with staged outputs and metadata tagging."""

import asyncio
import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from mutagen.flac import FLAC, Picture

from backend.audio.library import AudioLibrary, AudioLibraryError
from backend.core.config import Settings, get_settings
from backend.metadata.cover import CoverAsset, CoverStore
from backend.metadata.filenames import render_track_filename
from backend.models.export import ExportRequest
from backend.models.tracks import Track
from backend.tracks.store import TrackStateNotFoundError, TrackStore

ProgressReporter = Callable[[float, str], None]


class ExportError(RuntimeError):
    """Raised when an export cannot be completed safely."""


class ExportService:
    """Export the current manual segmentation without touching its source."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def validate_source(self, audio_id: str) -> None:
        try:
            AudioLibrary.instance().get(audio_id)
            TrackStore.instance().get(audio_id)
        except (AudioLibraryError, TrackStateNotFoundError) as exc:
            raise ExportError(str(exc)) from exc

    async def export(self, request: ExportRequest, report: ProgressReporter) -> dict[str, object]:
        try:
            source = AudioLibrary.instance().get(request.audio_id)
            collection = TrackStore.instance().get(request.audio_id)
        except (AudioLibraryError, TrackStateNotFoundError) as exc:
            raise ExportError(str(exc)) from exc

        destination = self._prepare_destination(request.destination)
        filenames = [
            render_track_filename(
                request.filename_template,
                track=track.number,
                artist=track.artist,
                title=track.title,
            )
            for track in collection.tracks
        ]
        covers = [
            (track, CoverStore.instance().get_optional(request.audio_id, track.id))
            for track in collection.tracks
        ]
        available_covers = [(track, cover) for track, cover in covers if cover is not None]
        cover_names = (
            self._cover_filenames(available_covers) if request.save_cover_file else []
        )
        self._validate_outputs(destination, [*filenames, *cover_names], request.overwrite)
        staging = destination / f".ats-export-{uuid4().hex}"
        await asyncio.to_thread(staging.mkdir, parents=False, exist_ok=False)
        staged_files: list[Path] = []
        final_files: list[Path] = []

        try:
            total = len(collection.tracks)
            for index, (track, filename) in enumerate(
                zip(collection.tracks, filenames, strict=True), start=1
            ):
                report((index - 1) / total * 96, f"Esportazione traccia {index} di {total}")
                staged = staging / filename
                await self._export_track(
                    source.path,
                    staged,
                    track,
                    request.compression_level,
                    index - 1,
                    total,
                    report,
                )
                if request.embed_metadata:
                    cover = CoverStore.instance().get_optional(request.audio_id, track.id)
                    await asyncio.to_thread(
                        self._write_flac_tags,
                        staged,
                        track,
                        total,
                        request.embed_metadata,
                        cover if request.embed_cover else None,
                    )
                elif request.embed_cover:
                    cover = CoverStore.instance().get_optional(request.audio_id, track.id)
                    if cover is not None:
                        await asyncio.to_thread(
                            self._write_flac_tags,
                            staged,
                            track,
                            total,
                            False,
                            cover,
                        )
                staged_files.append(staged)

            staged_cover_files: list[Path] = []
            if request.save_cover_file:
                for (_, cover), name in zip(available_covers, cover_names, strict=True):
                    staged_cover = staging / name
                    await asyncio.to_thread(shutil.copyfile, cover.path, staged_cover)
                    staged_cover_files.append(staged_cover)

            report(98, "Finalizzazione file…")
            for staged, filename in zip(staged_files, filenames, strict=True):
                final = destination / filename
                if final.exists() and not request.overwrite:
                    raise ExportError(f"Il file esiste già: {filename}")
                await asyncio.to_thread(os.replace, staged, final)
                final_files.append(final)
            final_cover_files: list[Path] = []
            for staged, filename in zip(staged_cover_files, cover_names, strict=True):
                final = destination / filename
                await asyncio.to_thread(os.replace, staged, final)
                final_cover_files.append(final)
            return {
                "destination": str(destination),
                "files": [str(path) for path in final_files],
                "count": len(final_files),
                "format": "flac",
                "audio_strategy": "lossless_reencode",
                "cover_files": [str(path) for path in final_cover_files],
            }
        finally:
            await asyncio.to_thread(shutil.rmtree, staging, True)

    def _prepare_destination(self, value: str) -> Path:
        destination = Path(value).expanduser()
        if not destination.is_absolute():
            raise ExportError("La cartella di destinazione deve essere un percorso assoluto.")
        destination = destination.resolve(strict=False)
        if destination == Path(destination.anchor):
            raise ExportError("Non è consentito esportare nella radice del disco.")
        cache = self.settings.cache_dir.resolve(strict=False)
        if destination == cache or cache in destination.parents:
            raise ExportError("La cartella di esportazione non può trovarsi nella cache applicativa.")
        try:
            destination.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ExportError(f"Impossibile creare la cartella di destinazione: {exc}") from exc
        if not destination.is_dir():
            raise ExportError("La destinazione selezionata non è una cartella.")
        return destination

    @staticmethod
    def _validate_outputs(destination: Path, filenames: list[str], overwrite: bool) -> None:
        normalized = [name.casefold() for name in filenames]
        if len(normalized) != len(set(normalized)):
            raise ExportError("Lo schema produce nomi file duplicati.")
        if not overwrite:
            existing = next((name for name in filenames if (destination / name).exists()), None)
            if existing:
                raise ExportError(f"Il file esiste già: {existing}")

    @staticmethod
    def _cover_filenames(covers: list[tuple[Track, CoverAsset]]) -> list[str]:
        if len(covers) == 1:
            return [f"cover{covers[0][1].path.suffix.lower()}"]
        return [f"{track.number:02d} - cover{cover.path.suffix.lower()}" for track, cover in covers]

    async def _export_track(
        self,
        source: Path,
        output: Path,
        track: Track,
        compression_level: int,
        completed_tracks: int,
        total_tracks: int,
        report: ProgressReporter,
    ) -> None:
        duration = track.end_seconds - track.start_seconds
        command = [
            self.settings.ffmpeg_binary,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-ss",
            f"{track.start_seconds:.3f}",
            "-i",
            str(source),
            "-t",
            f"{duration:.3f}",
            "-map",
            "0:a:0",
            "-vn",
            "-map_metadata",
            "-1",
            "-c:a",
            "flac",
            "-compression_level",
            str(compression_level),
            "-progress",
            "pipe:1",
            "-nostats",
            "-y",
            str(output),
        ]
        try:
            process = await asyncio.to_thread(
                subprocess.Popen,
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except FileNotFoundError as exc:
            raise ExportError("FFmpeg non è disponibile.") from exc

        output_lines: list[str] = []
        try:
            assert process.stdout is not None
            while True:
                line = await asyncio.to_thread(process.stdout.readline)
                if not line:
                    break
                stripped = line.strip()
                key, _, raw_value = stripped.partition("=")
                if key in {"out_time_us", "out_time_ms"}:
                    try:
                        elapsed = int(raw_value) / 1_000_000
                    except ValueError:
                        continue
                    within_track = min(1.0, elapsed / duration) if duration else 1.0
                    progress = (completed_tracks + within_track) / total_tracks * 96
                    report(progress, f"Esportazione traccia {completed_tracks + 1} di {total_tracks}")
                elif stripped:
                    output_lines.append(stripped)
                    output_lines = output_lines[-20:]
            return_code = await asyncio.to_thread(process.wait)
            if return_code != 0:
                error_text = "\n".join(output_lines)
                raise ExportError(error_text or "FFmpeg non ha completato l'esportazione.")
        except asyncio.CancelledError:
            if process.poll() is None:
                process.terminate()
                try:
                    await asyncio.wait_for(asyncio.to_thread(process.wait), timeout=5)
                except TimeoutError:
                    process.kill()
                    await asyncio.to_thread(process.wait)
            raise
        finally:
            if process.stdout is not None:
                process.stdout.close()

    @staticmethod
    def _write_flac_tags(
        path: Path,
        track: Track,
        total_tracks: int,
        embed_metadata: bool,
        cover: CoverAsset | None,
    ) -> None:
        audio = FLAC(path)
        audio.clear()
        audio.clear_pictures()
        if embed_metadata:
            tags = {
                "title": track.title,
                "artist": track.artist,
                "album": track.album,
                "albumartist": track.album_artist,
                "tracknumber": str(track.track_number or track.number),
                "tracktotal": str(total_tracks),
                "discnumber": str(track.disc_number) if track.disc_number else "",
                "date": track.date,
                "genre": track.genre,
                "comment": track.comment,
                "composer": track.composer,
                "musicbrainz_releasegroupid": track.release_group_id or "",
            }
            for key, value in tags.items():
                if value:
                    audio[key] = value
        if cover is not None:
            picture = Picture()
            picture.type = 3
            picture.mime = cover.mime_type
            picture.desc = "Front cover"
            picture.data = cover.path.read_bytes()
            audio.add_picture(picture)
        audio.save()
