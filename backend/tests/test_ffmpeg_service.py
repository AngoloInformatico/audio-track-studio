from pathlib import Path

import pytest

from backend.audio.ffmpeg_service import FFmpegError, parse_probe_payload


def test_parse_probe_payload_prefers_audio_stream_data(tmp_path: Path) -> None:
    source = tmp_path / "mix.flac"
    source.write_bytes(b"audio")
    payload = {
        "streams": [
            {
                "codec_type": "audio",
                "codec_name": "flac",
                "sample_rate": "96000",
                "channels": 2,
                "channel_layout": "stereo",
                "bits_per_raw_sample": "24",
                "duration": "62.5",
            }
        ],
        "format": {"format_name": "flac", "size": "123456", "bit_rate": "1500000"},
    }

    info = parse_probe_payload(payload, source, "Long Mix.flac")

    assert info.name == "Long Mix.flac"
    assert info.format == "FLAC"
    assert info.duration_seconds == 62.5
    assert info.sample_rate == 96000
    assert info.bit_depth == 24
    assert info.bitrate == 1_500_000


def test_parse_probe_payload_rejects_non_audio_file(tmp_path: Path) -> None:
    source = tmp_path / "video.mp4"
    source.write_bytes(b"video")

    with pytest.raises(FFmpegError, match="non contiene una traccia audio"):
        parse_probe_payload({"streams": [{"codec_type": "video"}]}, source)
