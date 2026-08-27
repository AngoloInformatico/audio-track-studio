# Audio Track Studio — Guida e specifica di progetto

> **Release Windows 1.0.2 — Fasi 1–8 complete**

![Audio Track Studio Release 1.0](docs/screenshot-release.png)

Audio Track Studio è un editor desktop locale per trasformare mix, compilation, concerti e
registrazioni lunghe in tracce curate. Offre waveform interattiva, marker manuali e suggeriti,
riconoscimento musicale opzionale, metadati e cover, esportazione lossless e progetti
`.atsproject` recuperabili.

## Installazione Windows

La distribuzione consigliata è disponibile nella pagina
[GitHub Releases](https://github.com/AngoloInformatico/audio-track-studio/releases/latest):

```text
AudioTrackStudio-Setup-1.0.2.exe
```

L'installer è per Windows 10/11 x64, non richiede privilegi amministrativi e installa
l'applicazione nel profilo dell'utente. Python, Node.js, npm, FFmpeg e ffprobe non sono richiesti:
sono già inclusi nella release. Se Microsoft Edge WebView2 Runtime non è presente, il setup
esegue il bootstrapper Evergreen ufficiale Microsoft incluso nel pacchetto.

È disponibile anche la versione portabile:

```text
AudioTrackStudio-Portable-1.0.2.zip
```

La release non è firmata con un certificato Authenticode commerciale; Windows SmartScreen può
quindi mostrare un avviso al primo avvio. Verificare che il file provenga dal canale di
distribuzione previsto prima di eseguirlo.

## Uso rapido

1. Avvia `Audio Track Studio` dall'icona.
2. Scegli o trascina un file FLAC, WAV, MP3, M4A o AAC.
3. Aggiungi manualmente i marker oppure usa `Analizza` e conferma i suggerimenti desiderati.
4. Correggi confini, artista, titolo, metadati e copertina.
5. Salva il lavoro come `.atsproject` oppure abilita autosave/recovery.
6. Apri `Esporta`, verifica destinazione e opzioni, quindi genera le tracce FLAC.

Il file sorgente non viene mai modificato. Il riconoscimento AcoustID e il recupero delle cover
sono le sole funzioni che possono usare Internet; editing, analisi, splitting, export e progetti
funzionano offline.

Se una traccia non viene riconosciuta, l'app conserva come fallback l'artista presente nella
sorgente oppure, se manca, il titolo/filename del file importato. Quando il file contiene una
copertina JPEG o PNG incorporata, la stessa immagine viene proposta automaticamente per tutte le
tracce che non hanno una cover manuale o recuperata online.

## Configurazione utente

Al primo avvio vengono create cache, log, progetti, recovery e il file:

```text
%LOCALAPPDATA%\AudioTrackStudio\config.json
```

Per abilitare AcoustID inserire la propria chiave applicazione in `acoustid_api_key`. È possibile
impostare anche `export_directory`. Le variabili `ACOUSTID_API_KEY`, `ATS_EXPORT_DIR`,
`ATS_DATA_DIR`, `ATS_FFMPEG_BINARY`, `ATS_FFPROBE_BINARY` e `ATS_FPCALC_BINARY` hanno priorità
sul file locale e sono pensate soprattutto per sviluppo e diagnostica.

`fpcalc`/Chromaprint non è incorporato nella release corrente: se non viene configurato,
l'interfaccia indica chiaramente che il riconoscimento non è disponibile e tutte le funzioni
manuali restano operative.

## Sviluppo e build

Prerequisiti di sviluppo: Python 3.11+, Node.js 20.19+, FFmpeg/ffprobe e, per generare il setup,
Inno Setup 6. Dopo aver creato `.venv` e installato `requirements-dev.txt`:

```powershell
cd frontend
npm install
cd ..
.\scripts\build_release.ps1 -Installer
```

In alternativa, da Python puoi avviare la stessa pipeline completa con:

```powershell
py GeneraExe.py
```

`GeneraExe.py` individua automaticamente la cartella del progetto ed esegue
`scripts\build_release.ps1 -Installer`.

La pipeline esegue test, Ruff, ESLint, Vitest, build Vite, PyInstaller e Inno Setup. Usa
obbligatoriamente [Icon/icon.ico](Icon/icon.ico) per eseguibile e installer. Per verificare una
release senza aprire la GUI:

```powershell
$env:ATS_SMOKE_REPORT = "C:\tmp\ats-smoke.json"
& ".\release\Audio Track Studio\Audio Track Studio.exe" --smoke-test
```

## Risoluzione problemi

- **SmartScreen segnala un'app sconosciuta:** la release non è firmata; distribuire tramite un
  canale fidato oppure applicare un certificato Authenticode nella propria pipeline.
- **La finestra non si apre:** reinstallare Microsoft Edge WebView2 Runtime o rieseguire il setup.
- **Backend non connesso:** consultare
  `%LOCALAPPDATA%\AudioTrackStudio\logs\audio-track-studio.log`.
- **FFmpeg non disponibile:** nella release ufficiale deve essere incorporato; eseguire lo smoke
  test e verificare che `_internal\tools` contenga `ffmpeg.exe` e `ffprobe.exe`.
- **Recognition non disponibile:** configurare chiave AcoustID e `fpcalc`; l'editing manuale non
  richiede questi prerequisiti.
- **Progetto con sorgente spostata:** selezionare la nuova posizione dello stesso file; dimensione,
  durata e SHA-256 vengono controllati prima del ripristino.

## Struttura principale

```text
backend/       API, audio, analisi, recognition, export e progetti
frontend/      interfaccia React/TypeScript
desktop/       wrapper pywebview e server locale lifecycle-managed
packaging/     specifica PyInstaller, metadata Windows e installer Inno Setup
scripts/       pipeline di build della release
Icon/          icona Windows canonica
docs/          guida sviluppo e screenshot
```

## Licenze

Il codice applicativo è distribuito con licenza GNU General Public License v3.0; consultare il
file `LICENSE` nella radice. Dipendenze e binari mantengono le rispettive licenze; consultare
`THIRD_PARTY_NOTICES.md` e la cartella `licenses` della release. La build FFmpeg incorporata è
GPLv3 e viene distribuita insieme al relativo testo di licenza e ai riferimenti al codice sorgente.

---

