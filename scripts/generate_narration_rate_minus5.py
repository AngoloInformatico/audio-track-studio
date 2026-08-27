"""Generate testo.txt with the original Italian voice at -5% speed."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "Codex_Work" / "VoceNarrante"
SOURCE = OUTPUT_DIR / "testo.txt"
TEMP_OUTPUT = OUTPUT_DIR / "audio_track_studio_voce_rate_minus5_tts.mp3"
OUTPUT = OUTPUT_DIR / "audio_track_studio_voce_rate_minus5_hq.mp3"


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    subprocess.run(
        [
            "py", "-3.13", "-m", "edge_tts",
            "--voice", "it-IT-DiegoNeural",
            "--rate=-5%",
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
