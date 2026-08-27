"""Optional Cover Art Archive client keyed by MusicBrainz release group."""

from uuid import UUID

import httpx

from backend.metadata.cover import CoverError, CoverStore


class CoverArtArchiveClient:
    base_url = "https://coverartarchive.org/release-group"

    async def fetch_front(self, release_group_id: str) -> bytes | None:
        try:
            mbid = str(UUID(release_group_id))
        except ValueError as exc:
            raise CoverError("L'identificatore MusicBrainz non è valido.") from exc
        url = f"{self.base_url}/{mbid}/front-500"
        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=30,
                headers={"User-Agent": "AudioTrackStudio/1.0.3 (local desktop application)"},
            ) as client, client.stream("GET", url) as response:
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                declared = int(response.headers.get("Content-Length", "0") or 0)
                if declared > CoverStore.maximum_bytes:
                    raise CoverError("La copertina remota supera il limite di 10 MB.")
                chunks: list[bytes] = []
                size = 0
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > CoverStore.maximum_bytes:
                        raise CoverError("La copertina remota supera il limite di 10 MB.")
                    chunks.append(chunk)
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            raise CoverError(
                "Cover Art Archive non è disponibile. Puoi caricare una copertina manualmente."
            ) from exc
        data = b"".join(chunks)
        CoverStore.detect_image(data)
        return data
