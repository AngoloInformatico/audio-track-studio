# Sviluppo locale

La specifica completa è disponibile in `README_GUIDA.md` nella radice. Questo documento descrive l'avvio delle funzionalità implementate nelle Fasi 1–8 e nella Release 1.0.3.

## Prerequisiti

- Python 3.11 o successivo
- Node.js 20.19 o successivo (Node 22 consigliato)
- FFmpeg e ffprobe disponibili nel `PATH`
- Chromaprint/fpcalc e una chiave applicazione AcoustID per il riconoscimento musicale

## Backend

Da PowerShell, nella radice del progetto:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m backend
```

L'API risponde esclusivamente su `http://127.0.0.1:8765`. La documentazione OpenAPI è disponibile in sviluppo all'indirizzo `http://127.0.0.1:8765/docs`.

## Frontend

In un secondo terminale:

```powershell
cd frontend
npm install
npm run dev
```

Aprire `http://127.0.0.1:5173`.

## Verifiche

```powershell
py -3.13 -m pytest
py -3.13 -m ruff check backend
cd frontend
npm run lint
npm run test
npm run build
```

Il test E2E della Fase 2 utilizza Microsoft Edge già installato e un file audio di prova esplicitamente indicato:

```powershell
npm run e2e:phase2 -- "C:\percorso\audio-di-test.wav" "C:\tmp\ats-phase2.png"
```

La prova E2E della Fase 3 esegue anche uno split reale in due file FLAC:

```powershell
npm run e2e:phase3 -- "C:\percorso\audio-di-test.wav" "C:\tmp\ats-export" "C:\tmp\ats-phase3.png"
```

La prova E2E della Fase 4 analizza un audio con transizioni distinguibili e applica manualmente i suggerimenti:

```powershell
npm run e2e:phase4 -- "C:\percorso\audio-con-transizioni.wav" "C:\tmp\ats-phase4.png"
```

La prova E2E della Fase 5 verifica il flusso singolo/batch e il fallback esplicito quando i prerequisiti non sono configurati:

```powershell
npm run e2e:phase5 -- "C:\percorso\audio-di-test.wav" "C:\tmp\ats-phase5.png"
```

La prova E2E della Fase 6 modifica tutti i metadati, carica una cover e verifica l’esportazione FLAC con `cover.jpg`:

```powershell
npm run e2e:phase6 -- "C:\percorso\audio.wav" "C:\percorso\cover.jpg" "C:\tmp\ats-phase6-export" "C:\tmp\ats-phase6.png"
```

La prova E2E della Fase 7 salva un progetto, verifica recenti e recovery, chiude la sessione e
riapre lo stesso progetto ricollegando la sorgente audio:

```powershell
npm run e2e:phase7 -- "C:\percorso\audio.wav" "C:\percorso\cover.jpg" "C:\tmp\ats-phase7.png"
```

## Build desktop portabile — Fase 8

La build Windows usa pywebview/WebView2 e PyInstaller in modalità one-folder. Il frontend statico,
FFmpeg, ffprobe, icona e licenze vengono incorporati automaticamente:

```powershell
.\scripts\build_release.ps1
```

La distribuzione viene creata in `dist\Audio Track Studio`. FFmpeg/ffprobe possono essere
indicati con i rispettivi override `ATS_*`.

Lo smoke test dell'eseguibile non apre finestre e non usa Python o FFmpeg esterni:

```powershell
$env:ATS_DATA_DIR = "C:\tmp\ats-release-smoke\data"
$env:ATS_SMOKE_REPORT = "C:\tmp\ats-release-smoke\report.json"
& ".\dist\Audio Track Studio\Audio Track Studio.exe" --smoke-test
```

## Stato delle Fasi 1–8

Disponibile:

- API health con verifica centralizzata di FFmpeg/ffprobe;
- importazione in streaming di FLAC, WAV, MP3, M4A e AAC;
- lettura dei dati tecnici tramite ffprobe;
- waveform zoomabile e player locale;
- marker aggiungibili con doppio clic o alla posizione del cursore;
- marker trascinabili e timestamp modificabili al millisecondo;
- anteprima audio prima, dopo e intorno al confine selezionato;
- tabella di tracce contigue con riproduzione, split e merge;
- modifica manuale inline di artista e titolo;
- tema Chiaro, Scuro e Sistema con preferenza persistente;
- shell desktop responsive da 1280×720.
- schermata riepilogativa di esportazione con percorso, naming, compressione e opzioni metadata;
- splitting asincrono in FLAC con avanzamento e annullamento;
- nomi file sanificati e controllo preventivo di duplicati/sovrascritture;
- tag FLAC titolo, artista e numero traccia tramite Mutagen;
- staging transazionale: i file parziali vengono rimossi in caso di errore o annullamento.
- analisi automatica asincrona e cancellabile, completamente locale;
- rilevamento combinato di silenzi/cali, variazioni energetiche e cambiamenti spettrali;
- sensibilità e distanza minima tra confini configurabili;
- confini suggeriti con confidenza e indicazione dei segnali rilevati;
- applicazione esplicita e selettiva dei suggerimenti ai marker esistenti.
- riconoscimento singolo o batch tramite fingerprint Chromaprint e lookup AcoustID;
- configurazione guidata della chiave AcoustID e installazione verificata di fpcalc dalla release ufficiale;
- candidati multipli con confidenza, album/data disponibili e selezione manuale;
- applicazione atomica e confermata di artista e titolo, con fallback alla modifica inline.
- editor completo per album, album artist, numeri traccia/disco, data, genere, commento e compositore;
- caricamento, anteprima, sostituzione e rimozione di copertine JPEG/PNG fino a 10 MB;
- recupero opzionale dal Cover Art Archive quando il riconoscimento fornisce un release-group MusicBrainz;
- tag FLAC avanzati e incorporamento della cover tramite Mutagen;
- salvataggio opzionale di `cover.jpg`, `cover.png` o file cover distinti per traccia.
- formato progetto JSON `.atsproject` versionato, senza duplicazione del file audio;
- salvataggio atomico, Salva con nome e download del documento dal browser;
- progetti recenti, autosave opzionale e snapshot di recovery;
- ripristino completo di marker, tracce, metadati, risultati recognition, tema e cover;
- ricollegamento guidato della sorgente spostata con verifica di dimensione e durata.
- wrapper desktop nativo pywebview con WebView2 e server API su porta loopback casuale;
- frontend di produzione, Python, FFmpeg e ffprobe incorporati nella cartella standalone;
- `Icon/icon.ico` applicata all'EXE, al setup, ai collegamenti e alla disinstallazione;
- installer Inno Setup per utente corrente con bootstrapper WebView2 condizionale;
- configurazione predefinita, log e cartelle dati creati al primo avvio;
- modalità smoke test per simulare una macchina priva di Python, Node e FFmpeg nel PATH.

La roadmap delle otto fasi è completa. La firma Authenticode resta un'attività della pipeline di
distribuzione perché richiede un certificato intestato al proprietario del software.

In modalità web di sviluppo, il browser non espone il percorso locale completo del file. L'importazione crea quindi una copia gestita nella cache applicativa, scritta a blocchi e rimossa quando la sessione viene chiusa. Il progetto conserva soltanto l'identità tecnica della sorgente e alla riapertura richiede il ricollegamento. Il futuro wrapper desktop potrà aprire direttamente il percorso autorizzato dall'utente, evitando questa copia per file molto grandi.

Per isolare cache, log, progetti e recovery durante test o installazioni portabili è possibile
impostare `ATS_DATA_DIR`. In assenza di override viene usata la directory locale applicativa
`AudioTrackStudio` dell'utente.

## Strategia audio della Fase 3

Lo split FLAC usa FFmpeg con ricodifica FLAC lossless. Questa scelta garantisce punti di taglio precisi al millisecondo e non introduce perdita qualitativa aggiuntiva. Non viene usato stream copy: anche quando il sorgente è FLAC, ogni segmento viene decodificato e ricodificato in FLAC, preservando sample rate e canali rilevati dal flusso sorgente. La compressione configurabile modifica solo dimensione e tempo di elaborazione, non la qualità.

L'output MP3 nativo e la relativa scelta tra stream copy e ricodifica di alta qualità restano una funzionalità successiva, come previsto dalla specifica completa.

## Analisi automatica della Fase 4

FFmpeg decodifica il primo flusso audio in mono a 11.025 Hz senza creare file intermedi. Il backend lavora su finestre da 500 ms e calcola RMS, centroide spettrale e flusso spettrale. Le sequenze a bassa energia e i picchi di novelty vengono uniti rispettando la distanza minima scelta dall'utente.

La confidenza misura la forza relativa degli indizi audio e non costituisce una certezza sul cambio di brano. L'analisi non modifica la suddivisione: i confini vengono mostrati come suggerimenti e diventano marker soltanto dopo la selezione e la conferma dell'utente. DJ mix, concerti e transizioni senza silenzio possono richiedere sensibilità maggiore e correzione manuale.
