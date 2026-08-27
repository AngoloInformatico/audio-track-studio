# Componenti di terze parti

Audio Track Studio utilizza componenti open source con licenze proprie, tra cui FastAPI
(MIT), Uvicorn (BSD-3-Clause), pywebview (BSD-3-Clause), pythonnet (MIT), React (MIT),
WaveSurfer.js (BSD-3-Clause), Mutagen (GPL-2.0-or-later), NumPy (BSD-3-Clause) e PyInstaller
(GPL-2.0-or-later con eccezione per la distribuzione dei programmi generati).

La release Windows incorpora `ffmpeg.exe` e `ffprobe.exe` dalla build Essentials di Gyan.dev,
compilata con opzioni GPLv3. La relativa licenza completa è distribuita nella cartella
`licenses` della release. Codice sorgente e informazioni di build sono disponibili presso:

- https://ffmpeg.org/
- https://www.gyan.dev/ffmpeg/builds/

Microsoft Edge WebView2 Runtime è un prerequisito del wrapper Windows. L'installer include
il bootstrapper Evergreen ufficiale Microsoft e lo esegue soltanto se il runtime non è già
presente.

La funzione **Imposta AcoustID** può scaricare su richiesta `fpcalc` dalla release ufficiale
Windows x64 di Chromaprint. Chromaprint è distribuito secondo GNU LGPL 2.1; il pacchetto
originale, compresi i relativi avvisi di licenza, viene conservato nella cartella locale gestita
dall'applicazione. Sorgenti e release sono disponibili presso:

- https://github.com/acoustid/chromaprint
- https://acoustid.org/chromaprint

Questo file è informativo e non sostituisce i testi di licenza originali dei singoli componenti.
