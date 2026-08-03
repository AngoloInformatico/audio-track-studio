# Audio Track Studio — Guida e specifica di progetto

> **Release Windows 1.0.1 — Fasi 1–8 complete**

![Audio Track Studio Release 1.0](docs/screenshot-release.png)

Audio Track Studio è un editor desktop locale per trasformare mix, compilation, concerti e
registrazioni lunghe in tracce curate. Offre waveform interattiva, marker manuali e suggeriti,
riconoscimento musicale opzionale, metadati e cover, esportazione lossless e progetti
`.atsproject` recuperabili.

## Installazione Windows

La distribuzione consigliata è disponibile nella pagina
[GitHub Releases](https://github.com/AngoloInformatico/audio-track-studio/releases/latest):

```text
AudioTrackStudio-Setup-1.0.1.exe
```

L'installer è per Windows 10/11 x64, non richiede privilegi amministrativi e installa
l'applicazione nel profilo dell'utente. Python, Node.js, npm, FFmpeg e ffprobe non sono richiesti:
sono già inclusi nella release. Se Microsoft Edge WebView2 Runtime non è presente, il setup
esegue il bootstrapper Evergreen ufficiale Microsoft incluso nel pacchetto.

È disponibile anche la versione portabile:

```text
AudioTrackStudio-Portable-1.0.1.zip
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

## Specifica di progetto per Codex

### 1. Obiettivo

Realizzare un'applicazione desktop moderna e riutilizzabile per Windows, denominata provvisoriamente **Audio Track Studio**, pensata principalmente per gestire file audio lunghi contenenti più brani musicali consecutivi.

Caso d'uso principale: un video/mix musicale di oltre un'ora è stato convertito in FLAC e contiene numerosi brani uniti uno dopo l'altro. L'applicazione deve aiutare l'utente a individuare i singoli brani, riconoscerli, correggere eventualmente i punti di separazione e infine esportarli come file audio separati con nome, tag e possibilmente copertina corretti.

Il progetto NON deve essere un semplice script usa-e-getta, ma un'applicazione completa, modulare e riutilizzabile in futuro.

---

## 2. Architettura generale

L'applicazione deve utilizzare:

- **Python come backend**
- **Frontend Web moderno** per l'interfaccia grafica
- comunicazione frontend/backend tramite API locali
- esecuzione interamente sul PC dell'utente per tutte le operazioni che non richiedono servizi online
- possibilità finale di distribuire l'app come normale applicazione Windows avviabile da icona, senza obbligare l'utente ad aprire manualmente terminale o browser.

### Stack preferito

#### Backend
- Python 3.11+ / 3.12+
- FastAPI
- Uvicorn per sviluppo
- FFmpeg / ffprobe
- Mutagen per metadati
- librerie audio Python solo quando realmente necessarie
- eventuale librosa per analisi avanzata
- eventuale pydub solo dove utile

#### Frontend
Preferenza per:
- React
- TypeScript
- Vite
- CSS moderno
- WaveSurfer.js per waveform e regioni/marker

Evitare un'interfaccia Python tradizionale (Tkinter, CustomTkinter, ecc.) come UI principale.

### Desktop wrapper

Valutare in fase di implementazione:

1. **Tauri + backend Python**, se l'integrazione risulta robusta e semplice da distribuire;
2. in alternativa **pywebview**, se permette una soluzione più affidabile e meno complessa.

L'obiettivo finale è che l'utente possa avviare `Audio Track Studio` come una normale applicazione desktop.

---

## 3. Principi fondamentali

Il sistema deve separare chiaramente tre problemi differenti:

1. **Rilevamento dei confini tra i brani**
2. **Riconoscimento di artista/titolo**
3. **Taglio/esportazione dell'audio**

Non assumere che tra due brani esista sempre silenzio.

Molti file possono essere:
- compilation;
- DJ mix;
- registrazioni da video;
- concerti;
- playlist concatenate;
- mix con crossfade;
- file nei quali un brano inizia mentre il precedente sta terminando.

Per questo motivo il rilevamento del silenzio deve essere soltanto uno dei segnali utilizzabili e NON l'unico metodo di separazione.

---

## 4. Formati audio

### Input inizialmente supportati

Obbligatori:
- FLAC
- WAV
- MP3
- M4A/AAC

Possibile estensione futura:
- OGG
- OPUS
- ALAC
- altri formati gestibili da FFmpeg

Il progetto nasce soprattutto per **FLAC e MP3**.

### Requisito obbligatorio: pieno supporto MP3

L'applicazione deve funzionare in modo completo anche quando il file sorgente è **MP3**, non soltanto FLAC.

Tutte le funzioni principali devono quindi essere disponibili sia per FLAC sia per MP3:

- apertura e analisi del file;
- lettura delle informazioni tecniche;
- generazione e visualizzazione della waveform;
- riproduzione e seek;
- rilevamento automatico dei possibili cambi di brano;
- creazione, modifica e spostamento dei marker;
- riconoscimento di artista e titolo;
- modifica dei metadati;
- gestione della copertina;
- suddivisione in singole tracce;
- esportazione;
- salvataggio e riapertura del progetto.

Per i file MP3 utilizzare correttamente i tag **ID3** tramite Mutagen o libreria equivalente.

Quando l'input è MP3, l'utente deve poter scegliere di esportare le singole tracce in **MP3** mantenendo, per quanto tecnicamente possibile, le caratteristiche e la qualità del file sorgente.

Poiché MP3 è un formato lossy, evitare ricodifiche multiple non necessarie. Se è tecnicamente possibile effettuare un taglio affidabile tramite stream copy, prevederlo; quando invece è necessaria la ricodifica per ottenere punti di taglio precisi, informare chiaramente l'utente e utilizzare impostazioni di qualità elevate/configurabili.

Il supporto MP3 deve essere considerato una funzionalità di prima classe dell'applicazione e deve essere testato con la stessa attenzione del supporto FLAC.

### Output

Priorità:
- FLAC

Prevedere eventualmente anche:
- WAV
- MP3
- AAC/M4A

Quando input e output lo permettono, preservare la qualità originale.

Per FLAC non deve esserci alcuna conversione verso formati lossy.

---

## 5. Importazione file

La schermata principale deve permettere:

- pulsante `Apri audio`
- drag & drop del file
- visualizzazione del nome file
- percorso
- formato
- durata
- sample rate
- bit depth quando disponibile
- numero canali
- bitrate quando significativo
- dimensione file

Usare `ffprobe` per ottenere informazioni tecniche affidabili.

---

## 6. Waveform

La waveform è una parte centrale dell'applicazione.

Deve essere:

- grande e facilmente leggibile;
- zoomabile;
- scorrevole orizzontalmente;
- sincronizzata con la riproduzione;
- dotata di cursore temporale;
- dotata di marker/regioni per i confini delle tracce;
- modificabile tramite mouse.

Preferenza: WaveSurfer.js.

### Marker

L'utente deve poter:

- aggiungere un marker;
- eliminare un marker;
- trascinare un marker;
- selezionare un marker;
- inserire manualmente il timestamp;
- effettuare zoom molto preciso intorno al marker.

Spostando un marker devono aggiornarsi automaticamente:
- fine della traccia precedente;
- inizio della traccia successiva;
- durata delle tracce interessate.

---

## 7. Riproduzione audio

Prevedere player integrato con:

- Play
- Pause
- Stop
- posizione corrente
- durata
- seek
- volume
- mute
- salto avanti/indietro

Funzioni molto utili durante l'editing:

- ascolta alcuni secondi prima del marker;
- ascolta alcuni secondi dopo il marker;
- ascolta il passaggio completo intorno al marker;
- riproduci solo la traccia selezionata.

Esempio:

`[ -10 sec ] [ ▶ Confine ] [ +10 sec ]`

La durata dell'anteprima deve essere configurabile.

---

## 8. Analisi automatica

Pulsante principale:

`Analizza`

Il backend deve analizzare il file cercando possibili cambi di brano.

Considerare una combinazione di tecniche, per esempio:

- silenzi;
- cali di volume;
- variazioni energetiche;
- cambiamenti spettrali;
- onset;
- novelty detection;
- variazioni timbriche;
- eventuali fingerprint su finestre temporali;
- altri metodi ritenuti affidabili.

Il risultato deve essere una serie di **confini suggeriti**, non necessariamente definitivi.

Ogni confine può avere un valore di confidenza.

Esempio:

| Confine | Timestamp | Confidenza |
|---|---:|---:|
| 1 | 04:12.850 | 92% |
| 2 | 08:37.210 | 76% |

L'utente deve sempre poter correggere manualmente il risultato.

---

## 9. Riconoscimento musicale

Pulsante:

`Riconosci tracce`

L'app deve tentare di identificare per ogni segmento:

- titolo;
- artista;
- album, quando disponibile;
- anno/data;
- numero traccia, se pertinente;
- genere, se disponibile;
- eventuale identificatore del servizio;
- copertina, se legalmente e tecnicamente disponibile.

### Tecnologie da valutare

Prima opzione da studiare:
- Chromaprint
- AcoustID

Valutare eventuali servizi alternativi se migliorano sensibilmente il riconoscimento.

IMPORTANTE: isolare il sistema di riconoscimento dietro un'interfaccia/provider, in modo da poter cambiare servizio in futuro senza riscrivere l'app.

Esempio concettuale:

```python
class MusicRecognitionProvider:
    def recognize(self, audio_segment):
        ...
```

Provider possibili:

```text
AcoustIDProvider
AltProvider
```

### Riconoscimento intelligente

Non inviare necessariamente l'intera traccia.

Il sistema può provare campioni significativi:
- parte iniziale;
- parte centrale;
- parte finale;
- più finestre se il primo tentativo fallisce.

Evitare, quando possibile, intro parlate, silenzi e transizioni.

---

## 10. Correlazione riconoscimento/confini

Questa è una funzione importante.

Il riconoscimento musicale non deve servire soltanto per assegnare il titolo.

Se analizzando finestre temporali consecutive cambia il fingerprint/brano riconosciuto, questa informazione può essere utilizzata come ulteriore indizio per determinare il punto di passaggio tra due tracce.

L'algoritmo deve quindi poter combinare:

`analisi audio + fingerprint + eventuali silenzi`

per proporre un confine più accurato.

Non è richiesto che la prima versione raggiunga la perfezione, ma l'architettura deve permettere di migliorare questo sistema.

---

## 11. Tabella tracce

Sotto o accanto alla waveform mostrare l'elenco delle tracce.

Esempio:

| # | Inizio | Fine | Durata | Artista | Titolo | Stato |
|---|---|---|---|---|---|---|
| 01 | 00:00.000 | 04:12.850 | 04:12 | Artist | Song | ✓ |
| 02 | 04:12.850 | 08:37.210 | 04:24 | Artist | Song | ✓ |

Ogni riga deve poter essere:

- selezionata;
- riprodotta;
- modificata;
- riconosciuta nuovamente;
- eliminata/unita;
- eventualmente divisa ulteriormente.

---

## 12. Editor metadati

Per ogni traccia prevedere campi modificabili:

- Titolo
- Artista
- Album
- Album Artist
- Track Number
- Disc Number
- Anno/Data
- Genere
- Commento
- Composer, se disponibile

I dati ottenuti automaticamente NON devono essere considerati immutabili.

L'utente deve poter correggere tutto prima dell'esportazione.

---

## 13. Copertine

Se disponibile attraverso le fonti utilizzate, mostrare la copertina.

Consentire:

- anteprima;
- sostituzione manuale;
- rimozione;
- incorporamento nel FLAC;
- eventuale salvataggio `cover.jpg` nella cartella di destinazione.

Non bloccare l'esportazione se la copertina non è disponibile.

---

## 14. Esportazione

Pulsante:

`Esporta`

Prima dell'esportazione mostrare una schermata riepilogativa.

Impostazioni:

- cartella destinazione;
- formato;
- schema nome file;
- sovrascrittura sì/no;
- incorporamento metadata;
- incorporamento cover;
- normalizzazione SOLO se esplicitamente richiesta.

Schema predefinito:

```text
{track:02d} - {artist} - {title}.flac
```

Esempio:

```text
01 - Queen - Radio Ga Ga.flac
02 - Toto - Africa.flac
03 - a-ha - Take On Me.flac
```

Sanificare automaticamente i caratteri non validi nei nomi Windows.

---

## 15. Qualità audio

La qualità è prioritaria.

Per file lossless:
- evitare elaborazioni non necessarie;
- non convertire mai automaticamente in formato lossy;
- mantenere sample rate e bit depth quando possibile;
- evitare normalizzazione o DSP automatici.

Per file MP3:
- preservare il bitrate/qualità originale quando possibile;
- evitare ricodifiche lossy ripetute;
- supportare correttamente metadata ID3 e cover art;
- permettere MP3 come formato di esportazione nativo;
- documentare quando viene usato stream copy e quando è necessaria una ricodifica.

Se per ottenere tagli precisi è necessaria una ricodifica FLAC, essa rimane comunque lossless.

Documentare chiaramente quando FFmpeg utilizza stream copy e quando effettua una nuova codifica lossless.

---

## 16. Modalità automatica e manuale

Prevedere due flussi.

### Automatica

Workflow:

```text
Apri file
    ↓
Analizza
    ↓
Trova possibili tracce
    ↓
Riconosci
    ↓
Verifica risultati
    ↓
Esporta
```

### Manuale

L'utente:
- apre il file;
- aggiunge i marker manualmente;
- ascolta i confini;
- inserisce/corregge artista e titolo;
- esporta.

Le due modalità devono poter essere mischiate liberamente.

---

## 17. Salvataggio progetto

L'utente deve poter salvare il lavoro senza esportare immediatamente.

Formato progetto, per esempio:

```text
*.atsproject
```

Può essere JSON o un contenitore appropriato.

Deve contenere almeno:
- riferimento al file sorgente;
- marker;
- tracce;
- metadati;
- impostazioni;
- risultati riconoscimento;
- eventuali modifiche manuali.

Prevedere:

- `Nuovo progetto`
- `Apri progetto`
- `Salva`
- `Salva con nome`

NON duplicare il grande file audio all'interno del progetto salvo esplicita necessità futura.

Gestire in modo chiaro il caso in cui il file sorgente sia stato spostato.

### Implementazione Fase 7 — formato v1

La Fase 7 usa un documento JSON versionato con estensione `.atsproject` e schema
`audio-track-studio-project` versione `1`. Il documento include riferimento descrittivo della
sorgente (nome, dimensione, durata, formato e impronta SHA-256), marker, intervalli e ID delle tracce, tutti i
metadati manuali, il risultato di riconoscimento selezionato, impostazioni del progetto e cover
JPEG/PNG deduplicate tramite SHA-256. Il contenuto audio e i percorsi della cache locale non
vengono mai incorporati.

I salvataggi e gli snapshot di recovery sono scritti atomicamente nella directory dati locale
dell'applicazione. La UI offre Nuovo progetto, Apri progetto, Salva, Salva con nome, progetti
recenti, download del file `.atsproject` e autosave opzionale. Alla riapertura il browser chiede
di ricollegare la sorgente: una copia identica può trovarsi in una posizione o avere un nome
diverso, mentre dimensione, durata o impronta non corrispondenti vengono rifiutate con un errore leggibile.
Il limite del documento è 64 MB; le funzioni progetto restano completamente offline.

---

## 18. Interfaccia grafica

La GUI deve avere un aspetto moderno e professionale.

NON deve sembrare un pannello amministrativo generico.

Tema visivo ispirato ad applicazioni audio moderne.

### Layout suggerito

#### Sidebar sinistra
- Home/Editor
- Progetti
- Esportazioni
- Impostazioni
- Informazioni

#### Top bar
- nome progetto/file
- Apri
- Salva
- Analizza
- Riconosci
- Esporta
- Light/Dark toggle

#### Area centrale
- informazioni file
- waveform
- timeline
- marker
- player
- tabella tracce

#### Pannello laterale destro opzionale
Quando una traccia è selezionata:
- cover;
- titolo;
- artista;
- metadata;
- confidence;
- azioni.

---

## 19. Light/Dark Mode

Obbligatorio.

Tre possibilità nelle impostazioni:

- Light
- Dark
- Sistema

Il tema deve essere implementato tramite variabili CSS/design tokens.

Esempio concettuale:

```css
:root {
  --background: ...;
  --surface: ...;
  --text: ...;
  --text-secondary: ...;
  --border: ...;
  --accent: ...;
}

[data-theme="dark"] {
  ...
}
```

Salvare la preferenza.

Se impostato su `Sistema`, seguire `prefers-color-scheme`.

Tutti i componenti, inclusa la waveform, devono adattarsi al tema.

---

## 20. Responsive design

L'app nasce per desktop.

Deve funzionare bene almeno da:
- 1280×720
- 1920×1080
- risoluzioni superiori

Gestire correttamente scaling Windows 125%, 150%, ecc.

Evitare elementi con dimensioni rigidamente dipendenti dai pixel quando non necessario.

---

## 21. UX

Implementare:

- tooltip;
- toast/notifiche;
- progress bar;
- skeleton/loading;
- dialog di conferma;
- errori leggibili;
- possibilità di annullare operazioni lunghe;
- indicatore attività backend;
- disabilitazione intelligente dei pulsanti.

Durante analisi:

```text
Analisi audio...
██████████████░░░░░ 72%
Analisi spettro: 38:21 / 52:47
```

Durante riconoscimento:

```text
Riconoscimento traccia 7 di 14
```

Durante esportazione:

```text
Esportazione 5 di 14
```

L'interfaccia NON deve bloccarsi durante elaborazioni lunghe.

---

## 22. Backend asincrono / job system

Analisi, riconoscimento ed esportazione possono durare minuti.

Non eseguirli nel thread/UI flow in modo bloccante.

Creare un semplice sistema di job backend con:
- ID job;
- stato;
- percentuale;
- messaggio;
- risultato;
- errore;
- cancellazione.

Possibili stati:

```text
pending
running
completed
failed
cancelled
```

Frontend e backend possono comunicare tramite:
- REST + polling inizialmente;
- WebSocket/SSE se utile.

Preferire semplicità e robustezza.

---

## 23. API

Strutturare FastAPI in endpoint logici.

Esempio indicativo:

```text
GET    /api/health
POST   /api/audio/open
GET    /api/audio/info
POST   /api/analysis/start
GET    /api/jobs/{id}
DELETE /api/jobs/{id}
POST   /api/recognition/start
POST   /api/tracks/{id}/recognize
PUT    /api/tracks/{id}
POST   /api/export/start
GET    /api/projects/recent
GET    /api/projects/recovery
POST   /api/projects/save
POST   /api/projects/autosave
POST   /api/projects/inspect
POST   /api/projects/prepare
POST   /api/projects/apply
GET    /api/projects/{id}/download
```

Non è obbligatorio utilizzare esattamente questi endpoint, ma mantenere API pulite e documentate.

---

## 24. Sicurezza locale

Il backend è locale.

Per impostazione predefinita:
- bind esclusivamente a `127.0.0.1`;
- NON esporre FastAPI sulla LAN;
- evitare CORS permissivo globale;
- validare tutti i percorsi file;
- impedire path traversal;
- validare input frontend.

---

## 25. Configurazione

Prevedere impostazioni persistenti:

- tema;
- ultima cartella aperta;
- cartella export;
- formato output predefinito;
- schema nome file;
- durata anteprima marker;
- sensibilità analisi;
- provider riconoscimento;
- eventuali API key;
- comportamento cover;
- lingua futura.

Le API key NON devono essere committate nel repository.

Utilizzare `.env` o storage locale sicuro appropriato.

Creare `.env.example`.

---

## 26. Logging

Implementare logging strutturato.

Livelli:
- DEBUG
- INFO
- WARNING
- ERROR

Creare file log con rotazione.

Non inserire API key nei log.

Aggiungere eventualmente un pulsante:

`Apri cartella log`

utile per diagnosi.

---

## 27. Gestione FFmpeg

All'avvio verificare:

- disponibilità `ffmpeg`;
- disponibilità `ffprobe`;
- versione.

Se non disponibili:
- mostrare un errore comprensibile;
- fornire istruzioni;
- oppure prevedere in futuro un bundle dell'eseguibile nella distribuzione Windows.

Centralizzare l'accesso a FFmpeg in un servizio Python dedicato.

NON spargere chiamate subprocess in tutto il codice.

---

## 28. Performance

Il file può durare diverse ore e pesare molti GB.

Quindi:
- non caricare l'intero audio non compresso in RAM se non necessario;
- usare streaming/chunk;
- generare waveform peaks/cache;
- riutilizzare risultati già calcolati;
- non rigenerare fingerprint inutilmente;
- mantenere l'interfaccia fluida.

Prevedere cache temporanea eliminabile.

---

## 29. Struttura progetto suggerita

```text
Audio-Track-Studio/
│
├── backend/
│   ├── main.py
│   ├── api/
│   │   ├── audio.py
│   │   ├── analysis.py
│   │   ├── recognition.py
│   │   ├── tracks.py
│   │   ├── projects.py
│   │   └── export.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── jobs.py
│   │
│   ├── audio/
│   │   ├── ffmpeg_service.py
│   │   ├── analyzer.py
│   │   ├── silence_detector.py
│   │   ├── boundary_detector.py
│   │   ├── waveform.py
│   │   ├── player.py
│   │   └── splitter.py
│   │
│   ├── recognition/
│   │   ├── base.py
│   │   ├── acoustid.py
│   │   └── service.py
│   │
│   ├── metadata/
│   │   ├── tags.py
│   │   ├── cover.py
│   │   └── filenames.py
│   │
│   ├── projects/
│   │   ├── models.py
│   │   └── storage.py
│   │
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── stores/
│   │   ├── types/
│   │   ├── styles/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── desktop/
│   └── eventuale wrapper Tauri/pywebview
│
├── assets/
│   ├── icons/
│   └── images/
│
├── docs/
├── scripts/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── LICENSE
```

Codex può modificare la struttura se esiste una soluzione tecnicamente migliore, purché rimangano separazione delle responsabilità e modularità.

---

## 30. Testing

Aggiungere test almeno per:

- parsing ffprobe;
- sanitizzazione nomi file;
- gestione timestamp;
- creazione segmenti;
- salvataggio/caricamento progetto;
- metadata;
- provider recognition mock;
- API principali.

Per il frontend aggiungere test sulle funzioni critiche, senza sovraccaricare inizialmente il progetto.

---

## 31. Error handling

Gestire chiaramente:

- file inesistente;
- formato non supportato;
- file corrotto;
- FFmpeg assente;
- errore fingerprint;
- Internet assente;
- servizio recognition non disponibile;
- API rate limit;
- nessun brano riconosciuto;
- cartella output non scrivibile;
- spazio disco insufficiente;
- progetto con sorgente spostata.

Il fallimento del riconoscimento NON deve impedire l'editing manuale o l'esportazione.

---

## 32. Funzionamento offline

Devono funzionare offline:

- apertura file;
- waveform;
- analisi locale;
- marker;
- player;
- editing;
- tag manuali;
- splitting;
- export;
- salvataggio progetto.

Le funzioni che richiedono Internet devono essere chiaramente indicate.

Se Internet manca, mostrare ad esempio:

`Riconoscimento online non disponibile. Puoi continuare manualmente.`

---

## 33. Primo avvio

Al primo avvio:

1. controllare dipendenze;
2. controllare FFmpeg;
3. creare directory applicazione;
4. creare configurazione predefinita;
5. verificare directory temporanea;
6. aprire la schermata principale.

Non mostrare procedure tecniche all'utente se tutto funziona.

---

## 34. Packaging Windows

Obiettivo finale:

```text
Audio Track Studio.exe
```

o installer Windows.

L'utente finale NON deve dover:
- installare Python;
- eseguire `pip install`;
- eseguire npm;
- aprire PowerShell;
- avviare Uvicorn manualmente.

La build di sviluppo può naturalmente richiedere questi strumenti.

Valutare:
- PyInstaller/Nuitka per backend;
- bundle frontend;
- Tauri oppure pywebview;
- eventuale FFmpeg bundled, rispettandone licenza e modalità di distribuzione.

---

## 35. README finale del repository

Quando il progetto sarà implementato, aggiornare questo README trasformandolo anche in documentazione utente con:

- descrizione;
- screenshot;
- funzionalità;
- requisiti sviluppo;
- installazione;
- avvio development;
- build;
- configurazione recognition;
- uso;
- troubleshooting;
- struttura progetto;
- roadmap;
- licenza.

---

## 36. Git

Creare `.gitignore` adeguato per:

```text
.venv/
venv/
__pycache__/
*.pyc
node_modules/
dist/
build/
.env
logs/
cache/
temp/
output/
*.atsproject
```

Non committare:
- API key;
- file audio;
- cache;
- build;
- log;
- dati temporanei.

---

## 37. Priorità di sviluppo

### Fase 1 — Fondamenta

- struttura repository;
- FastAPI;
- React/TypeScript/Vite;
- Light/Dark;
- apertura file;
- ffprobe;
- waveform;
- player.

### Fase 2 — Editor

- marker;
- regioni;
- tabella tracce;
- editing timestamp;
- preview confini;
- gestione manuale tracce.

### Fase 3 — Splitting

- FFmpeg;
- esportazione FLAC;
- progress;
- cancellazione;
- naming;
- metadata.

### Fase 4 — Analisi automatica

- silence/energy/spectral detection;
- suggerimento confini;
- confidence;
- regolazione sensibilità.

### Fase 5 — Recognition

- Chromaprint;
- AcoustID;
- provider abstraction;
- metadata automatici;
- riconoscimento per singola traccia e batch.

### Fase 6 — Cover e metadata avanzati

- cover;
- album;
- anno;
- genre;
- editor completo.

### Fase 7 — Progetti

- `.atsproject`;
- autosave opzionale;
- recent projects;
- recovery.

### Fase 8 — Desktop/Release

- wrapper;
- build Windows;
- icona;
- installer;
- test macchina pulita.

---

## 38. Requisiti UX importanti

Non considerare il risultato dell'analisi automatica come definitivo.

Il principio dell'app deve essere:

> **L'automazione propone, l'utente mantiene il controllo.**

L'utente deve poter intervenire in qualsiasi momento.

Non nascondere i timestamp.

Non applicare modifiche distruttive al file sorgente.

Il file originale deve rimanere sempre intatto.

---

## 39. Requisiti di qualità del codice

Codex deve:

- evitare file monolitici;
- usare type hints Python;
- usare TypeScript, non JavaScript non tipizzato, per il frontend;
- documentare classi/funzioni non ovvie;
- mantenere backend e frontend disaccoppiati;
- evitare duplicazione;
- centralizzare configurazione;
- centralizzare FFmpeg;
- centralizzare chiamate API frontend;
- gestire correttamente async/thread/process;
- non bloccare la UI;
- utilizzare nomi chiari;
- non inserire placeholder lasciati indefinitamente.

---

## 40. Indicazioni specifiche per Codex

Quando inizi il progetto:

1. Leggi integralmente questo README.
2. Non creare tutto in un singolo file.
3. Prepara prima l'architettura.
4. Implementa una fase alla volta.
5. Dopo ogni fase esegui test/lint/build.
6. Non rimuovere funzioni già funzionanti per semplificare una fase successiva.
7. Non simulare come funzionanti caratteristiche non ancora implementate.
8. Se una feature non è pronta, indicarla chiaramente come non disponibile.
9. Mantieni il progetto eseguibile durante lo sviluppo.
10. Prima della release finale verifica il workflow completo con un vero file audio lungo.
11. Non modificare mai il file audio sorgente.
12. Privilegia affidabilità e qualità audio rispetto alla velocità di implementazione.
13. Non usare servizi a pagamento senza che siano opzionali e chiaramente configurabili.
14. Preferisci componenti e librerie open source affidabili.
15. Documenta eventuali prerequisiti esterni.

---

## 41. Risultato finale atteso

L'utente deve poter:

1. avviare Audio Track Studio;
2. trascinare dentro un file FLAC o MP3 di oltre un'ora;
3. vedere immediatamente informazioni e waveform;
4. premere `Analizza`;
5. ottenere una prima suddivisione proposta;
6. premere `Riconosci tracce`;
7. ottenere, quando possibile, artista e titolo;
8. ascoltare ogni confine;
9. spostare manualmente i marker sbagliati;
10. correggere metadata;
11. scegliere la cartella di destinazione;
12. premere `Esporta`;
13. ottenere file separati come:

```text
01 - Artista - Titolo.flac
02 - Artista - Titolo.flac
03 - Artista - Titolo.flac
...
```

con metadata FLAC corretti e, quando disponibile, copertina incorporata.

Il tutto senza alterare il file originale e senza perdita di qualità audio.

---

## 42. Possibili sviluppi futuri

L'architettura deve lasciare spazio, senza implementarli necessariamente nella prima release, a:

- MusicBrainz;
- Discogs o altri provider metadata compatibili con relative condizioni d'uso;
- riconoscimento alternativo;
- editing CUE sheet;
- import/export CUE;
- batch processing;
- auto-tag di cartelle;
- rilevamento BPM;
- tonalità musicale;
- ReplayGain;
- spettrogramma;
- lyrics;
- plugin/provider system;
- localizzazione multilingua;
- macOS/Linux;
- aggiornamenti automatici.

Queste funzioni NON devono complicare inutilmente la prima versione.

---

# Regola principale

**Costruire prima un editor audio affidabile e utilizzabile manualmente; aggiungere poi automazione e riconoscimento.**

Il programma deve essere utile anche se il riconoscimento online fallisce completamente.
