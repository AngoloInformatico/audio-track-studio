"""Generate a smooth single-voice narration from testo.txt."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "Codex_Work" / "VoceNarrante"
SOURCE = OUTPUT_DIR / "testo.txt"
TEMP_OUTPUT = OUTPUT_DIR / "audio_track_studio_voce_youtube_single_fast_tts.mp3"
OUTPUT = OUTPUT_DIR / "audio_track_studio_voce_youtube_single_fast_hq.mp3"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    text = SOURCE.read_text(encoding="utf-8")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"([.!?])(?=[A-ZÀÈÉÌÒÙ])", r"\1 ", text)

    subprocess.run(
        [
            "py", "-3.13", "-m", "edge_tts",
            "--voice", "it-IT-DiegoNeural",
            "--rate=+4%",
            "--pitch=+0Hz",
            "--text", text,
            "--write-media", str(TEMP_OUTPUT),
        ],
        check=True,
    )
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(TEMP_OUTPUT),
            "-codec:a", "libmp3lame", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            str(OUTPUT),
        ],
        check=True,
    )
    print(f"Creato: {OUTPUT}")


if __name__ == "__main__":
    main()
