$ErrorActionPreference = "Stop"

$outputMp3 = Join-Path $PSScriptRoot "..\audio_track_studio_voce_narrante_podcast.mp3"

$text = @"
Hai mai avuto un lungo mix musicale, una registrazione dal vivo o una compilation con tutti i brani riuniti in un unico file?

Audio Track Studio nasce per risolvere esattamente questo problema.

È un’applicazione desktop per Windows progettata per trasformare registrazioni audio di lunga durata in tracce singole, ordinate e complete di informazioni.

Audio Track Studio è stato progettato e sviluppato da Alex Lignola, con l’obiettivo di offrire uno strumento preciso, affidabile e semplice da utilizzare. Il software è disponibile gratuitamente nei repository GitHub ufficiali di AngoloInformatico, insieme alla documentazione e alle istruzioni per il download.

Per iniziare basta trascinare il file all’interno dell’applicazione oppure selezionarlo dal computer. Sono supportati i principali formati audio: FLAC, WAV, MP3, M4A e AAC.

Durante l’importazione vengono visualizzate le informazioni tecniche principali, tra cui formato, durata, frequenza di campionamento, profondità in bit, numero di canali, bitrate e dimensione del file.

Un aspetto fondamentale è la protezione del sorgente: il file audio originale non viene mai modificato.

Una volta aperto il file, Audio Track Studio mostra la waveform completa della registrazione. È possibile ascoltare l’audio, spostarsi nella timeline, utilizzare i comandi di riproduzione, regolare il volume e aumentare lo zoom per lavorare con maggiore precisione.

Per individuare i possibili cambi di brano è disponibile la funzione Analizza. L’elaborazione viene eseguita localmente e combina diversi indizi audio, come silenzi, cali di volume, variazioni energetiche e cambiamenti spettrali.

Il risultato è una serie di confini suggeriti, ciascuno accompagnato da un livello di confidenza. I suggerimenti non vengono applicati automaticamente: l’utente può selezionare solo quelli ritenuti corretti.

Questa modalità è particolarmente utile con compilation, mix DJ e registrazioni in cui i brani sono collegati da transizioni o crossfade, senza pause nette.

Dopo l’analisi, ogni marker può essere spostato manualmente sulla waveform oppure modificato inserendo il timestamp con precisione al millisecondo. Le tracce adiacenti vengono aggiornate automaticamente, così inizio, fine e durata rimangono sempre coerenti.

È inoltre possibile dividere una traccia in un punto preciso oppure unirla alla traccia successiva.

La tabella delle tracce offre una panoramica completa del progetto. Per ogni segmento sono visibili numero, inizio, fine, durata, artista, titolo e stato. Ogni traccia può essere riprodotta singolarmente, modificata oppure inviata al riconoscimento musicale.

Quando configurato, il riconoscimento utilizza Chromaprint e AcoustID per cercare artista, titolo, album e data. L’applicazione analizza brevi campioni della traccia e propone i risultati disponibili, che devono essere confermati manualmente.

Se il riconoscimento online non è disponibile, tutte le funzioni di editing manuale continuano comunque a funzionare.

Per ogni traccia è possibile modificare titolo, artista, album, numero traccia, genere, data, compositore, commento e altri campi. È possibile inoltre associare una copertina caricandola dal computer oppure recuperandola online, quando disponibile.

Il lavoro può essere salvato in un progetto Audio Track Studio, con supporto per autosave e recovery. Il progetto conserva le modifiche senza duplicare il file audio originale.

Quando tutto è pronto, basta aprire la sezione Esporta. Audio Track Studio genera file FLAC separati, con nomi personalizzabili, metadati incorporabili e, quando disponibile, la relativa copertina.

L’esportazione è lossless: la qualità audio non viene degradata.

Da un unico lungo mix si ottiene così una raccolta di tracce ordinate, curate e pronte per essere archiviate, ascoltate o importate in un altro lettore musicale.

Audio Track Studio: più controllo sui tuoi file audio, più precisione nel montaggio e nessuna modifica al sorgente originale.
"@

py -3.13 -m edge_tts --voice "it-IT-GiuseppeMultilingualNeural" --rate="-12%" --pitch="-1Hz" --text $text --write-media $outputMp3
if ($LASTEXITCODE -ne 0) { throw "La sintesi vocale online non ha prodotto il file MP3." }

$outputHq = Join-Path $PSScriptRoot "..\audio_track_studio_voce_narrante_podcast_hq.mp3"
ffmpeg -hide_banner -loglevel error -y -i $outputMp3 -codec:a libmp3lame -b:a 192k -ar 44100 -ac 2 $outputHq
if ($LASTEXITCODE -ne 0) { throw "La conversione finale MP3 non è riuscita." }
Write-Output "Creato: $outputHq"
