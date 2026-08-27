"""Generate a social-style Italian narration with explicit English term clips."""

from __future__ import annotations

import asyncio
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "Codex_Work" / "VoceNarrante"
OUTPUT_FILE = OUTPUT_DIR / "audio_track_studio_voce_social_mixed_hq.mp3"

ITALIAN_VOICE = "it-IT-DiegoNeural"
ENGLISH_VOICE = "en-US-GuyNeural"


def it(text: str) -> tuple[str, str]:
    return ("it", text)


def en(text: str) -> tuple[str, str]:
    return ("en", text)


SEGMENTS: list[tuple[str, str]] = [
    it("Hai mai avuto un lungo "),
    en("mix"),
    it(" musicale, una registrazione dal vivo o una compilation con tutti i brani riuniti in un unico "),
    en("file?\n\n"),
    en("Audio Track Studio"),
    it(" nasce per risolvere esattamente questo problema.\n\n"),
    it("È un’applicazione desktop per "),
    en("Windows"),
    it(" progettata per trasformare registrazioni audio di lunga durata in tracce singole, ordinate e complete di informazioni.\n\n"),
    it("Audio Track Studio è stato progettato e sviluppato da Alex Lignola, con l’obiettivo di offrire uno strumento preciso, affidabile e semplice da utilizzare. Il software è disponibile gratuitamente nei repository "),
    en("GitHub"),
    it(" ufficiali di AngoloInformatico, insieme alla documentazione e alle istruzioni per il "),
    en("download"),
    it(".\n\n"),
    it("Per iniziare basta trascinare il "),
    en("file"),
    it(" all’interno dell’applicazione oppure selezionarlo dal computer. Sono supportati i principali formati audio: FLAC, WAV, MP3, M4A e AAC.\n\n"),
    it("Durante l’importazione vengono visualizzate le informazioni tecniche principali, tra cui formato, durata, frequenza di campionamento, profondità in bit, numero di canali, bitrate e dimensione del "),
    en("file"),
    it(".\n\nUn aspetto fondamentale è la protezione del sorgente: il "),
    en("file"),
    it(" audio originale non viene mai modificato.\n\n"),
    it("Una volta aperto il "),
    en("file"),
    it(", Audio Track Studio mostra la "),
    en("waveform"),
    it(" completa della registrazione. È possibile ascoltare l’audio, spostarsi nella "),
    en("timeline"),
    it(", utilizzare i comandi di riproduzione, regolare il volume e aumentare lo zoom per lavorare con maggiore precisione.\n\n"),
    it("Per individuare i possibili cambi di brano è disponibile la funzione Analizza. L’elaborazione viene eseguita localmente e combina diversi indizi audio, come silenzi, cali di volume, variazioni energetiche e cambiamenti spettrali.\n\n"),
    it("Il risultato è una serie di confini suggeriti, ciascuno accompagnato da un livello di confidenza. I suggerimenti non vengono applicati automaticamente: l’utente può selezionare solo quelli ritenuti corretti.\n\n"),
    it("Questa modalità è particolarmente utile con compilation, "),
    en("mix DJ"),
    it(" e registrazioni in cui i brani sono collegati da transizioni o "),
    en("crossfade"),
    it(", senza pause nette.\n\n"),
    it("Dopo l’analisi, ogni "),
    en("marker"),
    it(" può essere spostato manualmente sulla "),
    en("waveform"),
    it(" oppure modificato inserendo il "),
    en("timestamp"),
    it(" con precisione al millisecondo. Le tracce adiacenti vengono aggiornate automaticamente, così inizio, fine e durata rimangono sempre coerenti.\n\n"),
    it("È inoltre possibile dividere una traccia in un punto preciso oppure unirla alla traccia successiva.\n\n"),
    it("La tabella delle tracce offre una panoramica completa del progetto. Per ogni segmento sono visibili numero, inizio, fine, durata, artista, titolo e stato. Ogni traccia può essere riprodotta singolarmente, modificata oppure inviata al riconoscimento musicale.\n\n"),
    it("Quando configurato, il riconoscimento utilizza Chromaprint e AcoustID per cercare artista, titolo, album e data. L’applicazione analizza brevi campioni della traccia e propone i risultati disponibili, che devono essere confermati manualmente.\n\n"),
    it("Se il riconoscimento "),
    en("online"),
    it(" non è disponibile, tutte le funzioni di "),
    en("editing"),
    it(" manuale continuano comunque a funzionare.\n\n"),
    it("Per ogni traccia è possibile modificare titolo, artista, album, numero traccia, genere, data, compositore, commento e altri campi. È possibile inoltre associare una "),
    en("cover"),
    it(" caricandola dal computer oppure recuperandola "),
    en("online"),
    it(", quando disponibile.\n\n"),
    it("Il lavoro può essere salvato in un progetto Audio Track Studio, con supporto per "),
    en("autosave"),
    it(" e "),
    en("recovery"),
    it(". Il progetto conserva le modifiche senza duplicare il "),
    en("file"),
    it(" audio originale.\n\n"),
    it("Quando tutto è pronto, basta aprire la sezione Esporta. Audio Track Studio genera "),
    en("file FLAC"),
    it(" separati, con nomi personalizzabili, metadati incorporabili e, quando disponibile, la relativa "),
    en("cover"),
    it(".\n\n"),
    it("L’esportazione è "),
    en("lossless"),
    it(": la qualità audio non viene degradata.\n\n"),
    it("Da un unico lungo "),
    en("mix"),
    it(" si ottiene così una raccolta di tracce ordinate, curate e pronte per essere archiviate, ascoltate o importate in un altro lettore musicale.\n\n"),
    en("Audio Track Studio"),
    it(": più controllo sui tuoi file audio, più precisione nel montaggio e nessuna modifica al sorgente originale."),
]


def render_segment(index: int, language: str, text: str, directory: Path) -> Path:
    voice = ITALIAN_VOICE if language == "it" else ENGLISH_VOICE
    rate = "+6%" if language == "it" else "-2%"
    pitch = "+1Hz" if language == "it" else "+0Hz"
    destination = directory / f"segment_{index:03d}.mp3"
    if not any(character.isalnum() for character in text):
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=channel_layout=mono:sample_rate=24000",
                "-t",
                "0.18",
                "-codec:a",
                "libmp3lame",
                "-b:a",
                "48k",
                str(destination),
            ],
            check=True,
        )
        return destination
    subprocess.run(
        [
            "py",
            "-3.13",
            "-m",
            "edge_tts",
            "--voice",
            voice,
            f"--rate={rate}",
            f"--pitch={pitch}",
            "--text",
            text,
            "--write-media",
            str(destination),
        ],
        check=True,
    )
    return destination


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ats-narration-") as temp:
        segment_dir = Path(temp)
        paths: list[Path] = []
        for index, (language, text) in enumerate(SEGMENTS, start=1):
            paths.append(render_segment(index, language, text, segment_dir))

        concat_file = segment_dir / "concat.txt"
        concat_file.write_text(
            "\n".join(f"file '{path.as_posix()}'" for path in paths),
            encoding="utf-8",
        )
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "192k",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(OUTPUT_FILE),
        ]
        subprocess.run(command, check=True)

    print(f"Creato: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
