"""Create a faster YouTube narration from Codex_Work/VoceNarrante/testo.txt."""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "Codex_Work" / "VoceNarrante"
SOURCE = OUTPUT_DIR / "testo.txt"
OUTPUT = OUTPUT_DIR / "audio_track_studio_voce_youtube_fast_hq.mp3"

ITALIAN_VOICE = "it-IT-DiegoNeural"
ENGLISH_VOICE = "en-US-GuyNeural"

ENGLISH_TERMS = [
    "Audio Track Studio",
    "file FLAC",
    "file audio",
    "sample rate",
    "mix DJ",
    "crossfade",
    "Audio Track Studio",
    "Windows",
    "GitHub",
    "download",
    "compilation",
    "desktop",
    "live",
    "file",
    "waveform",
    "timeline",
    "zoom",
    "marker",
    "timestamp",
    "online",
    "autosave",
    "recovery",
    "lossless",
    "mix",
    "cache",
    "bitrate",
    "tag",
]
ENGLISH_TERMS = sorted(set(ENGLISH_TERMS), key=len, reverse=True)
TERM_PATTERN = re.compile("|".join(re.escape(term) for term in ENGLISH_TERMS), re.IGNORECASE)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"([.!?])(?=[A-ZÀÈÉÌÒÙ])", r"\1 ", text)
    return text


def split_segments(text: str) -> list[tuple[str, str]]:
    segments: list[tuple[str, str]] = []
    cursor = 0
    for match in TERM_PATTERN.finditer(text):
        if match.start() > cursor:
            segments.append(("it", text[cursor : match.start()]))
        segments.append(("en", match.group(0)))
        cursor = match.end()
    if cursor < len(text):
        segments.append(("it", text[cursor:]))
    return [(language, value) for language, value in segments if value.strip()]


def render_segment(index: int, language: str, text: str, directory: Path) -> Path:
    destination = directory / f"segment_{index:03d}.mp3"
    if not any(character.isalnum() for character in text):
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "anullsrc=channel_layout=mono:sample_rate=24000",
                "-t", "0.10", "-codec:a", "libmp3lame", "-b:a", "48k",
                str(destination),
            ],
            check=True,
        )
        return destination

    voice = ITALIAN_VOICE if language == "it" else ENGLISH_VOICE
    # Faster, energetic Italian delivery for YouTube; slightly slower English inserts for clarity.
    rate = "+18%" if language == "it" else "+8%"
    pitch = "+1Hz" if language == "it" else "+0Hz"
    subprocess.run(
        [
            "py", "-3.13", "-m", "edge_tts",
            "--voice", voice,
            f"--rate={rate}",
            f"--pitch={pitch}",
            "--text", text,
            "--write-media", str(destination),
        ],
        check=True,
    )
    return destination


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    segments = split_segments(normalize_text(SOURCE.read_text(encoding="utf-8")))
    with tempfile.TemporaryDirectory(prefix="ats-youtube-narration-") as temporary:
        directory = Path(temporary)
        paths = [
            render_segment(index, language, value, directory)
            for index, (language, value) in enumerate(segments, start=1)
        ]
        concat_file = directory / "concat.txt"
        concat_file.write_text(
            "\n".join(f"file '{path.as_posix()}'" for path in paths),
            encoding="utf-8",
        )
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat_file),
                "-codec:a", "libmp3lame", "-b:a", "192k", "-ar", "44100", "-ac", "2",
                str(OUTPUT),
            ],
            check=True,
        )
    print(f"Creato: {OUTPUT}")


if __name__ == "__main__":
    main()
