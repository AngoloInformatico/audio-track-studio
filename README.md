# Audio Track Studio

> Editor desktop locale per suddividere registrazioni audio lunghe in tracce curate.

[![Versione](https://img.shields.io/badge/versione-1.0.3-2f81f7?style=for-the-badge)](https://github.com/AngoloInformatico/audio-track-studio/releases/latest)
![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011-0078d4?style=for-the-badge&logo=windows11&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776ab?style=for-the-badge&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-TypeScript-20232a?style=for-the-badge&logo=react&logoColor=61dafb)
[![Licenza](https://img.shields.io/badge/licenza-GPLv3-2ea44f?style=for-the-badge)](LICENSE)

![Audio Track Studio Release 1.0.3](docs/screenshot-release.png)

Audio Track Studio combina waveform interattiva, marker manuali e suggeriti, metadati,
copertine e progetti recuperabili in un'applicazione Windows. Il file sorgente non viene mai
modificato e le tracce vengono esportate in FLAC lossless.

## Funzionalità principali

- importazione FLAC, WAV, MP3, M4A e AAC;
- waveform zoomabile con riproduzione e marker modificabili al millisecondo;
- analisi locale di silenzi, energia e variazioni spettrali;
- suddivisione, unione e anteprima dei confini delle tracce;
- editor di artista, titolo, album, numerazione, genere, commenti e copertine;
- riconoscimento musicale opzionale tramite Chromaprint e AcoustID, con configurazione guidata;
- esportazione asincrona in FLAC con avanzamento e annullamento;
- salvataggio, autosave e recovery dei progetti `.atsproject`;
- tema chiaro, scuro o di sistema;
- applicazione desktop Windows basata su pywebview e WebView2.

## Download

Scarica la versione portabile dalla pagina
[GitHub Releases](https://github.com/AngoloInformatico/audio-track-studio/releases/latest).

- `AUDIO-TRACK-STUDIO-v1.0.3-Windows.zip`: applicazione completa per Windows 10/11 x64,
  da estrarre interamente prima dell'avvio.

La release non è firmata con un certificato Authenticode commerciale; Windows SmartScreen può
mostrare un avviso al primo avvio.

## Architettura

```text
backend/       API FastAPI, audio, analisi, recognition, export e progetti
frontend/      interfaccia React e TypeScript
desktop/       wrapper pywebview e server locale
packaging/     configurazione PyInstaller e metadati Windows
scripts/       strumenti di build e pubblicazione
Icon/          icona Windows
docs/          documentazione di sviluppo e screenshot
```

Il backend è esposto esclusivamente sull'interfaccia loopback. Editing, analisi, splitting,
esportazione e gestione dei progetti funzionano offline; soltanto AcoustID e il recupero delle
copertine possono accedere a Internet.

## Configurazione AcoustID

Apri **Imposta AcoustID** nel menu laterale dell'applicazione. Da questa finestra puoi:

- inserire o sostituire la chiave applicazione AcoustID;
- scaricare e configurare con un clic la release ufficiale Windows x64 di Chromaprint/fpcalc;
- indicare manualmente un `fpcalc.exe` già presente sul PC;
- verificare lo stato completo tramite la spunta verde.

La chiave viene salvata localmente in `%LOCALAPPDATA%\AudioTrackStudio\config.json` e non viene
mai restituita dall'API. La copia gestita di fpcalc viene conservata in
`%LOCALAPPDATA%\AudioTrackStudio\tools`; non è un file di cache e non viene duplicata a ogni
analisi. `ACOUSTID_API_KEY` e `ATS_FPCALC_BINARY` restano disponibili come override avanzati per
lo sviluppo.

La procedura dettagliata completa è disponibile in
[README_GUIDA.md](README_GUIDA.md#configurazione-guidata-acoustid).

## Avvio in sviluppo

### Prerequisiti

- Python 3.11 o successivo;
- Node.js 20.19 o successivo;
- FFmpeg e ffprobe disponibili nel `PATH`;
- facoltativi: fpcalc/Chromaprint e una chiave applicazione AcoustID.

Da PowerShell, nella radice del progetto:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
python -m backend
```

In un secondo terminale:

```powershell
cd frontend
npm install
npm run dev
```

Aprire `http://127.0.0.1:5173`. La documentazione OpenAPI del backend è disponibile in sviluppo
su `http://127.0.0.1:8765/docs`.

## Verifiche

```powershell
py -3.13 -m pytest
py -3.13 -m ruff check backend
cd frontend
npm run lint
npm run test
npm run build
```

## Build Windows

Per creare la versione portabile:

```powershell
.\scripts\build_release.ps1
```

In alternativa:

```powershell
py GeneraExe.py
```

La versione portabile viene generata in `dist/Audio Track Studio/`, pronta per essere
compressa e pubblicata da GitPilot. La directory `dist/` è un artefatto locale e non è
versionata nel repository.

## Documentazione

- [Guida e specifica completa](README_GUIDA.md)
- [Sviluppo locale e test](docs/development.md)
- [Avvisi sulle dipendenze di terze parti](THIRD_PARTY_NOTICES.md)

## Licenza

Audio Track Studio è distribuito con licenza
[GNU General Public License v3.0](LICENSE). Puoi usare, studiare, modificare e ridistribuire il
software nel rispetto dei termini della GPLv3. Le dipendenze e i binari di terze parti mantengono
le rispettive licenze indicate in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
