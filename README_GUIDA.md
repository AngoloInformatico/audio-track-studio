# Audio Track Studio — Guida e specifica di progetto

> **Release Windows 1.0.3 — Fasi 1–8 complete**

![Audio Track Studio Release 1.0.3](docs/screenshot-release.png)

Audio Track Studio è un editor desktop locale per trasformare mix, compilation, concerti e
registrazioni lunghe in tracce curate. Offre waveform interattiva, marker manuali e suggeriti,
riconoscimento musicale opzionale, metadati e cover, esportazione lossless e progetti
`.atsproject` recuperabili.

## Versione portabile Windows

La distribuzione consigliata è disponibile nella pagina
[GitHub Releases](https://github.com/AngoloInformatico/audio-track-studio/releases/latest):

```text
AUDIO-TRACK-STUDIO-v1.0.3-Windows.zip
```

Estrarre interamente lo ZIP e avviare `Audio Track Studio.exe` senza separarlo dalla cartella
`_internal`. Python, Node.js, npm, FFmpeg e ffprobe non sono richiesti perché sono inclusi.
È necessario Microsoft Edge WebView2 Runtime, normalmente già presente in Windows 10/11.

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

## Configurazione guidata AcoustID

Per attivare il riconoscimento musicale sono necessari una **Application API Key** AcoustID e
`fpcalc`, lo strumento di fingerprinting incluso nel progetto Chromaprint. Audio Track Studio
permette di configurare entrambi senza modificare manualmente file o variabili di sistema.

1. Avvia Audio Track Studio e seleziona **Imposta AcoustID** nel menu laterale.
2. Nella sezione **Chiave API AcoustID**, usa il collegamento **Ottieni una chiave gratuita**.
3. Accedi ad AcoustID e registra Audio Track Studio nella pagina
   [New Application](https://acoustid.org/new-application).
4. Copia la **Application API Key** generata. Non usare la User API Key mostrata nel profilo,
   perché è destinata alla presentazione di nuovi fingerprint e non alle ricerche dell'app.
5. Incolla la chiave nel campo **Chiave applicazione** e premi **Salva chiave**.
6. Nella sezione **fpcalc / Chromaprint**, premi
   **Scarica e configura Chromaprint 1.6.1**. L'app scarica la release ufficiale Windows x64,
   verifica `fpcalc.exe` e configura automaticamente il percorso interno.
7. Quando entrambi i requisiti sono validi compare la spunta verde
   **Configurazione completata**. A questo punto puoi aprire un audio e usare **Riconosci**.

Se `fpcalc.exe` è già installato, espandi **Ho già fpcalc: configura il percorso manualmente**,
inserisci il percorso completo dell'eseguibile e premi **Verifica e usa percorso**.

La configurazione automatica non modifica il `PATH` di Windows e non richiede privilegi di
amministratore. Chromaprint viene installato una sola volta in:

```text
%LOCALAPPDATA%\AudioTrackStudio\tools\chromaprint-1.6.1
```

La chiave e il percorso vengono memorizzati localmente in:

```text
%LOCALAPPDATA%\AudioTrackStudio\config.json
```

Questo file si trova fuori dalla cartella del repository e non viene incluso nei commit o nei
push GitHub. La chiave non viene restituita dall'API locale né mostrata nuovamente
nell'interfaccia. Non copiare mai una chiave reale in `.env.example`, nel README o nei sorgenti.

L'uso del servizio AcoustID è gratuito per applicazioni non commerciali, nel rispetto delle
[linee guida del Web Service](https://acoustid.org/webservice). Il riconoscimento richiede una
connessione Internet; fingerprinting, analisi ed elaborazione audio restano locali.

## Configurazione utente avanzata

Al primo avvio vengono creati log, progetti, recovery e il file:

```text
%LOCALAPPDATA%\AudioTrackStudio\config.json
```

La finestra **Imposta AcoustID** aggiorna `acoustid_api_key` e `fpcalc_path`. È possibile
impostare anche `export_directory`. Le variabili `ACOUSTID_API_KEY`, `ATS_EXPORT_DIR`,
`ATS_DATA_DIR`, `ATS_FFMPEG_BINARY`, `ATS_FFPROBE_BINARY` e `ATS_FPCALC_BINARY` hanno priorità
sul file locale e sono pensate soprattutto per sviluppo e diagnostica.

`fpcalc`/Chromaprint viene scaricato soltanto su richiesta tramite il menu e non è duplicato a
ogni analisi. Se non viene configurato, l'interfaccia indica chiaramente che il riconoscimento
non è disponibile e tutte le funzioni manuali restano operative.

## Sviluppo e build

Prerequisiti di sviluppo: Python 3.11+, Node.js 20.19+ e FFmpeg/ffprobe. Dopo aver creato
`.venv` e installato `requirements-dev.txt`:

```powershell
cd frontend
npm install
cd ..
.\scripts\build_release.ps1
```

In alternativa, da Python puoi avviare la stessa pipeline completa con:

```powershell
py GeneraExe.py
```

`GeneraExe.py` individua automaticamente la cartella del progetto ed esegue
`scripts\build_release.ps1`.

La pipeline esegue test, Ruff, ESLint, Vitest, build Vite e PyInstaller. Usa obbligatoriamente
[Icon/icon.ico](Icon/icon.ico) per l'eseguibile. Per verificare una release senza aprire la GUI:

```powershell
$env:ATS_SMOKE_REPORT = "C:\tmp\ats-smoke.json"
& ".\dist\Audio Track Studio\Audio Track Studio.exe" --smoke-test
```

## Risoluzione problemi

- **SmartScreen segnala un'app sconosciuta:** la release non è firmata; distribuire tramite un
  canale fidato oppure applicare un certificato Authenticode nella propria pipeline.
- **La finestra non si apre:** installare o ripristinare Microsoft Edge WebView2 Runtime.
- **Backend non connesso:** consultare
  `%LOCALAPPDATA%\AudioTrackStudio\logs\audio-track-studio.log`.
- **FFmpeg non disponibile:** nella release ufficiale deve essere incorporato; eseguire lo smoke
  test e verificare che `_internal\tools` contenga `ffmpeg.exe` e `ffprobe.exe`.
- **Recognition non disponibile:** aprire **Imposta AcoustID** e verificare che entrambe le righe
  mostrino lo stato pronto e la spunta verde; l'editing manuale non richiede questi prerequisiti.
- **Progetto con sorgente spostata:** selezionare la nuova posizione dello stesso file; dimensione,
  durata e SHA-256 vengono controllati prima del ripristino.

## Struttura principale

```text
backend/       API, audio, analisi, recognition, export e progetti
frontend/      interfaccia React/TypeScript
desktop/       wrapper pywebview e server locale lifecycle-managed
packaging/     specifica PyInstaller e metadata Windows
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
