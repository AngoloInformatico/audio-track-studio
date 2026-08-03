import asyncio

import httpx

from backend.audio.ffmpeg_service import FFmpegService
from backend.main import app
from backend.models.health import ToolStatus
from backend.models.recognition import RecognitionConfig
from backend.recognition.acoustid import AcoustIDProvider
from backend.tracks.store import TrackStore


def test_health_endpoint_reports_dependencies(monkeypatch) -> None:
    async def inspect_tools(_: FFmpegService) -> dict[str, ToolStatus]:
        available = ToolStatus(available=True, version="test version")
        return {"ffmpeg": available, "ffprobe": available}

    monkeypatch.setattr(FFmpegService, "inspect_tools", inspect_tools)
    response = _request("GET", "/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["tools"]["ffprobe"]["available"] is True


def test_open_audio_rejects_unsupported_extension() -> None:
    response = _request(
        "POST",
        "/api/audio/open",
        files={"file": ("notes.txt", b"not audio", "text/plain")},
    )

    assert response.status_code == 400
    assert "Formato non supportato" in response.json()["detail"]


def test_project_inspection_rejects_invalid_document() -> None:
    response = _request(
        "POST",
        "/api/projects/inspect",
        files={"file": ("broken.atsproject", b"not json", "application/json")},
    )

    assert response.status_code == 422
    assert "non è valido" in response.json()["detail"]


def test_analysis_config_describes_editable_local_method() -> None:
    response = _request("GET", "/api/analysis/config")

    assert response.status_code == 200
    assert response.json()["default_sensitivity"] == 55
    assert "suggerimenti modificabili" in response.json()["method_note"]


def test_recognition_config_reports_missing_prerequisite(monkeypatch) -> None:
    async def inspect(_: AcoustIDProvider) -> RecognitionConfig:
        return RecognitionConfig(
            available=False,
            fpcalc_available=False,
            api_key_configured=False,
            message="Configurazione mancante.",
        )

    monkeypatch.setattr(AcoustIDProvider, "inspect", inspect)
    response = _request("GET", "/api/recognition/config")

    assert response.status_code == 200
    assert response.json()["provider"] == "acoustid"
    assert response.json()["available"] is False


def test_marker_and_track_endpoints_share_atomic_state() -> None:
    store = TrackStore.instance()
    store.initialize("api-audio", 240.0)
    try:
        response = _request("PUT", "/api/audio/api-audio/markers", json={"markers": [60.0, 150.5]})
        assert response.status_code == 200
        assert len(response.json()["tracks"]) == 3

        track_id = response.json()["tracks"][1]["id"]
        updated = _request(
            "PATCH",
            f"/api/audio/api-audio/tracks/{track_id}",
            json={"artist": "  Artist  ", "title": "  Song  "},
        )
        assert updated.status_code == 200
        assert updated.json()["tracks"][1]["artist"] == "Artist"
        assert updated.json()["tracks"][1]["title"] == "Song"

        fetched = _request("GET", "/api/audio/api-audio/tracks")
        assert fetched.json() == updated.json()
    finally:
        store.remove("api-audio")


def _request(method: str, url: str, **kwargs) -> httpx.Response:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, url, **kwargs)

    return asyncio.run(send())
