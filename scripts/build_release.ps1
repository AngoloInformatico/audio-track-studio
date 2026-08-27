param(
    [switch]$SkipTests,
    [switch]$Installer
)

$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$icon = Join-Path $projectRoot 'Icon\icon.ico'
$frontend = Join-Path $projectRoot 'frontend'
$dist = Join-Path $projectRoot 'dist'
$release = Join-Path $projectRoot 'release'

if (-not (Test-Path -LiteralPath $python)) { throw 'Ambiente virtuale .venv non trovato.' }
if (-not (Test-Path -LiteralPath $icon)) { throw 'Icon/icon.ico non trovato.' }

if (-not $SkipTests) {
    & $python -B -m pytest
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python -B -m ruff check backend desktop desktop_main.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Push-Location $frontend
    try {
        npm run lint
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        npm run test
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    } finally { Pop-Location }
}

Push-Location $frontend
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally { Pop-Location }

Push-Location $projectRoot
try {
    & $python -B -m PyInstaller --noconfirm --clean --distpath $dist --workpath (Join-Path $projectRoot 'build\pyinstaller') 'packaging\audio_track_studio.spec'
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally { Pop-Location }

$executable = Join-Path $dist 'Audio Track Studio\Audio Track Studio.exe'
if (-not (Test-Path -LiteralPath $executable)) { throw 'Build desktop non generata.' }
Write-Output "Release desktop: $executable"

if ($Installer) {
    $bootstrapper = Join-Path $projectRoot 'packaging\MicrosoftEdgeWebview2Setup.exe'
    if (-not (Test-Path -LiteralPath $bootstrapper)) {
        throw 'Bootstrapper WebView2 mancante in packaging\MicrosoftEdgeWebview2Setup.exe.'
    }
    $compilerCandidates = @(
        $env:ATS_ISCC_BINARY,
        'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
        'C:\Program Files\Inno Setup 6\ISCC.exe',
        (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe')
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
    $compiler = $compilerCandidates | Select-Object -First 1
    if (-not $compiler) { throw 'Inno Setup 6 non trovato. Imposta ATS_ISCC_BINARY.' }
    & $compiler (Join-Path $projectRoot 'packaging\installer.iss')
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Output "Installer: $(Join-Path $release 'installer\AudioTrackStudio-Setup-1.0.3.exe')"
}
