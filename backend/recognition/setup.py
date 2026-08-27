"""Local AcoustID configuration and managed Chromaprint installation."""

import asyncio
import os
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

import httpx

from backend.core.config import Settings, get_settings, update_user_config
from backend.models.recognition import AcoustIDSetupStatus, AcoustIDSetupUpdate
from backend.recognition.acoustid import AcoustIDProvider

CHROMAPRINT_VERSION = "1.6.1"
CHROMAPRINT_DOWNLOAD_URL = (
    "https://github.com/acoustid/chromaprint/releases/download/"
    "v1.6.1/chromaprint-fpcalc-1.6.1-windows-x86_64.zip"
)
MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024
MAX_EXTRACTED_BYTES = 150 * 1024 * 1024
MAX_ARCHIVE_FILES = 100


class AcoustIDSetupError(RuntimeError):
    """A safe, user-facing setup failure."""


class AcoustIDSetupService:
    _install_lock = asyncio.Lock()

    async def inspect(self) -> AcoustIDSetupStatus:
        settings = get_settings()
        readiness = await AcoustIDProvider(settings).inspect()
        binary = Path(settings.fpcalc_binary).expanduser()
        resolved = str(binary.resolve()) if binary.is_file() else settings.fpcalc_binary
        tools_directory = (settings.data_dir / "tools").resolve()
        managed = binary.is_file() and binary.resolve().is_relative_to(tools_directory)
        return AcoustIDSetupStatus(
            available=readiness.available,
            api_key_configured=readiness.api_key_configured,
            fpcalc_available=readiness.fpcalc_available,
            fpcalc_version=readiness.fpcalc_version,
            fpcalc_path=resolved,
            fpcalc_managed=managed,
            chromaprint_version=CHROMAPRINT_VERSION,
            message=readiness.message,
        )

    async def update(self, request: AcoustIDSetupUpdate) -> AcoustIDSetupStatus:
        updates: dict[str, object] = {}
        if request.acoustid_api_key is not None:
            api_key = request.acoustid_api_key.strip()
            if not api_key:
                raise AcoustIDSetupError("Inserisci una chiave AcoustID valida.")
            updates["acoustid_api_key"] = api_key
        if request.fpcalc_path is not None:
            path = Path(request.fpcalc_path.strip().strip('"')).expanduser()
            if not path.is_absolute() or not path.is_file():
                raise AcoustIDSetupError("Il percorso indicato non contiene un file fpcalc valido.")
            version = await self._inspect_binary(path)
            if version is None:
                raise AcoustIDSetupError("Il file selezionato non è un eseguibile fpcalc funzionante.")
            updates["fpcalc_path"] = str(path.resolve())
        if updates:
            update_user_config(updates)
        return await self.inspect()

    async def install_fpcalc(self) -> AcoustIDSetupStatus:
        if os.name != "nt":
            raise AcoustIDSetupError("L'installazione automatica è disponibile solo su Windows.")
        async with self._install_lock:
            settings = get_settings()
            target = settings.data_dir / "tools" / f"chromaprint-{CHROMAPRINT_VERSION}"
            existing = target / "fpcalc.exe"
            if existing.is_file() and await self._inspect_binary(existing):
                update_user_config({"fpcalc_path": str(existing.resolve())})
                return await self.inspect()

            settings.runtime_dir.mkdir(parents=True, exist_ok=True)
            staging = Path(tempfile.mkdtemp(prefix="chromaprint-", dir=settings.runtime_dir))
            archive = staging / "chromaprint.zip"
            extracted = staging / "extracted"
            try:
                await self._download(archive)
                fpcalc = await asyncio.to_thread(self._extract_archive, archive, extracted)
                if await self._inspect_binary(fpcalc) is None:
                    raise AcoustIDSetupError("Il pacchetto scaricato non contiene un fpcalc funzionante.")
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    await asyncio.to_thread(shutil.rmtree, target)
                await asyncio.to_thread(shutil.copytree, extracted, target)
                installed = target / fpcalc.relative_to(extracted)
                if await self._inspect_binary(installed) is None:
                    await asyncio.to_thread(shutil.rmtree, target, True)
                    raise AcoustIDSetupError("Chromaprint non ha superato la verifica dopo l'installazione.")
                update_user_config({"fpcalc_path": str(installed.resolve())})
            finally:
                await asyncio.to_thread(shutil.rmtree, staging, True)
            return await self.inspect()

    @staticmethod
    async def _inspect_binary(path: Path) -> str | None:
        provider = AcoustIDProvider(Settings(fpcalc_binary=str(path)))
        return await provider._inspect_fpcalc()

    @staticmethod
    async def _download(destination: Path) -> None:
        downloaded = 0
        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=httpx.Timeout(90, connect=20),
                headers={"User-Agent": "AudioTrackStudio/1.0.3"},
            ) as client, client.stream("GET", CHROMAPRINT_DOWNLOAD_URL) as response:
                response.raise_for_status()
                length = response.headers.get("Content-Length")
                if length and int(length) > MAX_DOWNLOAD_BYTES:
                    raise AcoustIDSetupError("Il pacchetto Chromaprint supera la dimensione prevista.")
                with destination.open("wb") as output:
                    async for chunk in response.aiter_bytes():
                        downloaded += len(chunk)
                        if downloaded > MAX_DOWNLOAD_BYTES:
                            raise AcoustIDSetupError("Download Chromaprint interrotto: file troppo grande.")
                        output.write(chunk)
        except AcoustIDSetupError:
            raise
        except (httpx.HTTPError, OSError, ValueError) as exc:
            raise AcoustIDSetupError(
                "Impossibile scaricare Chromaprint dalla release ufficiale. "
                "Controlla la connessione e riprova."
            ) from exc

    @staticmethod
    def _extract_archive(archive: Path, destination: Path) -> Path:
        destination.mkdir(parents=True, exist_ok=True)
        destination_root = destination.resolve()
        try:
            with zipfile.ZipFile(archive) as package:
                files = [item for item in package.infolist() if not item.is_dir()]
                if len(files) > MAX_ARCHIVE_FILES:
                    raise AcoustIDSetupError("Il pacchetto Chromaprint contiene troppi file.")
                if sum(item.file_size for item in files) > MAX_EXTRACTED_BYTES:
                    raise AcoustIDSetupError("Il pacchetto Chromaprint è più grande del previsto.")
                for item in files:
                    relative = PurePosixPath(item.filename)
                    if relative.is_absolute() or ".." in relative.parts:
                        raise AcoustIDSetupError("Il pacchetto Chromaprint contiene percorsi non sicuri.")
                    output = (destination / Path(*relative.parts)).resolve()
                    if not output.is_relative_to(destination_root):
                        raise AcoustIDSetupError("Il pacchetto Chromaprint contiene percorsi non sicuri.")
                    output.parent.mkdir(parents=True, exist_ok=True)
                    with package.open(item) as source, output.open("wb") as target:
                        shutil.copyfileobj(source, target)
        except AcoustIDSetupError:
            raise
        except (OSError, zipfile.BadZipFile) as exc:
            raise AcoustIDSetupError("Il pacchetto Chromaprint scaricato non è valido.") from exc
        candidates = list(destination.rglob("fpcalc.exe"))
        if len(candidates) != 1:
            raise AcoustIDSetupError("Nel pacchetto Chromaprint non è stato trovato fpcalc.exe.")
        return candidates[0]
