$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\")).Path
$image = Join-Path $root "docs\screenshot-release.png"
$audio = Join-Path $root "Codex_Work\VoceNarrante\VoceNarrante.mp3"
$output = Join-Path $root "Codex_Work\VoceNarrante\AudioTrackStudio_YouTube_1080p.mp4"

if (-not (Test-Path -LiteralPath $image)) { throw "Screenshot dell'app non trovato: $image" }
if (-not (Test-Path -LiteralPath $audio)) { throw "Voce narrante non trovata: $audio" }

$font = "C\:/Windows/Fonts/segoeui.ttf"
$fontBold = "C\:/Windows/Fonts/segoeuib.ttf"
$filter = @"
color=c=0x0b100f:s=1920x1080:r=30[base];
[0:v]scale=1480:795:flags=lanczos[shot];
[base][shot]overlay=380:135:format=auto,
drawbox=x=380:y=135:w=1480:h=795:color=0xf4774c@0.36:t=2,
drawbox=x=160:y=900:w=1600:h=140:color=0x111917@0.96:t=fill,
drawbox=x=160:y=900:w=1600:h=140:color=0x32433d@1:t=2,
drawtext=fontfile='$fontBold':text='AUDIO TRACK STUDIO':fontcolor=0xf4774c:fontsize=24:x=160:y=52,
drawtext=fontfile='$font':text='Editor audio locale per trasformare i mix in tracce curate':fontcolor=0xe8efeb:fontsize=28:x=160:y=82,
drawtext=fontfile='$font':text='Audio Track Studio  /  Alex Lignola  /  AngoloInformatico':fontcolor=0x91a29b:fontsize=20:x=160:y=1010,
drawtext=fontfile='$fontBold':text='IMPORTAZIONE E FORMATI AUDIO':fontcolor=0xffffff:fontsize=38:x=160:y=925:enable='between(t,0,35)',
drawtext=fontfile='$font':text='FLAC  /  MP3  /  WAV  /  M4A  /  AAC':fontcolor=0xf7a37f:fontsize=25:x=160:y=970:enable='between(t,0,35)',
drawtext=fontfile='$fontBold':text='INFORMAZIONI TECNICHE A COLPO D OCCHIO':fontcolor=0xffffff:fontsize=38:x=160:y=925:enable='between(t,35,70)',
drawtext=fontfile='$font':text='Durata  /  sample rate  /  bitrate  /  canali  /  sorgente protetto':fontcolor=0xf7a37f:fontsize=25:x=160:y=970:enable='between(t,35,70)',
drawtext=fontfile='$fontBold':text='WAVEFORM E RIPRODUZIONE PRECISA':fontcolor=0xffffff:fontsize=38:x=160:y=925:enable='between(t,70,110)',
drawtext=fontfile='$font':text='Timeline, zoom, volume e ascolto di ogni passaggio':fontcolor=0xf7a37f:fontsize=25:x=160:y=970:enable='between(t,70,110)',
drawtext=fontfile='$fontBold':text='ANALISI AUTOMATICA DEI CONFINI':fontcolor=0xffffff:fontsize=38:x=160:y=925:enable='between(t,110,155)',
drawtext=fontfile='$font':text='Silenzi, energia e variazioni spettrali diventano suggerimenti editabili':fontcolor=0xf7a37f:fontsize=25:x=160:y=970:enable='between(t,110,155)',
drawtext=fontfile='$fontBold':text='MARKER PRECISI E MODIFICABILI':fontcolor=0xffffff:fontsize=38:x=160:y=925:enable='between(t,155,205)',
drawtext=fontfile='$font':text='Confini al millisecondo, divisione, unione e anteprima delle tracce':fontcolor=0xf7a37f:fontsize=25:x=160:y=970:enable='between(t,155,205)',
drawtext=fontfile='$fontBold':text='METADATI, COPERTINE E RICONOSCIMENTO':fontcolor=0xffffff:fontsize=38:x=160:y=925:enable='between(t,205,250)',
drawtext=fontfile='$font':text='Artista, titolo, album, cover e informazioni personalizzabili':fontcolor=0xf7a37f:fontsize=25:x=160:y=970:enable='between(t,205,250)',
drawtext=fontfile='$fontBold':text='PROGETTI E RECOVERY':fontcolor=0xffffff:fontsize=38:x=160:y=925:enable='between(t,250,275)',
drawtext=fontfile='$font':text='Salvataggio .atsproject, autosave e recupero del lavoro':fontcolor=0xf7a37f:fontsize=25:x=160:y=970:enable='between(t,250,275)',
drawtext=fontfile='$fontBold':text='ESPORTAZIONE FLAC LOSSLESS':fontcolor=0xffffff:fontsize=38:x=160:y=925:enable='between(t,275,301)',
drawtext=fontfile='$font':text='Tracce separate, tag incorporabili e nessuna perdita di qualita':fontcolor=0xf7a37f:fontsize=25:x=160:y=970:enable='between(t,275,301)',
drawbox=x=160:y=1040:w=1600:h=5:color=0xf4774c@0.82:t=fill[v];
[1:a]showwaves=s=1560x112:mode=cline:colors=0xf4774c:rate=30:scale=lin[wave];
[v][wave]overlay=180:914:format=auto[vout]
"@

ffmpeg -hide_banner -y -loop 1 -i $image -i $audio -filter_complex $filter -map "[vout]" -map 1:a:0 -c:v libx264 -preset ultrafast -tune stillimage -crf 21 -pix_fmt yuv420p -r 30 -threads 0 -c:a aac -b:a 192k -shortest -movflags +faststart $output
if ($LASTEXITCODE -ne 0) { throw "Il render video non è riuscito." }
Write-Output "Creato: $output"
