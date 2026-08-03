[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)?$')]
    [string]$Repository,

    [ValidateSet('private', 'public')]
    [string]$Visibility = 'private',

    [string]$Description = 'Editor desktop locale per suddividere registrazioni audio lunghe in tracce curate.',

    [string]$CommitMessage = 'Initial import of Audio Track Studio',

    [switch]$Publish,

    [switch]$Yes
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Set-Location -LiteralPath $projectRoot

function Assert-Command {
    param([Parameter(Mandatory = $true)][string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Comando '$Name' non trovato nel PATH."
    }
}

function Assert-GitSuccess {
    param([Parameter(Mandatory = $true)][string]$Action)

    if ($LASTEXITCODE -ne 0) {
        throw "$Action non riuscita (codice $LASTEXITCODE)."
    }
}

function Resolve-GitHubCli {
    $installedCommand = Get-Command 'gh' -ErrorAction SilentlyContinue
    if ($installedCommand) {
        return $installedCommand.Source
    }

    $portableCommand = Join-Path $projectRoot '.tools\gh\gh.exe'
    if (Test-Path -LiteralPath $portableCommand -PathType Leaf) {
        return $portableCommand
    }

    throw "GitHub CLI non trovata. Installala oppure copia gh.exe in '.tools\gh\gh.exe'."
}

Assert-Command -Name 'git'

# Codex e altri ambienti isolati possono usare un account Windows diverso dal proprietario
# della cartella. Questa eccezione vale soltanto per il processo corrente e per questo progetto.
$env:GIT_CONFIG_COUNT = '1'
$env:GIT_CONFIG_KEY_0 = 'safe.directory'
$env:GIT_CONFIG_VALUE_0 = $projectRoot

if (-not (Test-Path -LiteralPath (Join-Path $projectRoot '.git'))) {
    & git init
    Assert-GitSuccess -Action 'Inizializzazione Git'
}

& git add --all
Assert-GitSuccess -Action 'Preparazione dei file Git'

$trackedPaths = @(& git ls-files)
Assert-GitSuccess -Action 'Lettura dei file Git'

if ($trackedPaths.Count -eq 0) {
    throw "Nessun file da pubblicare dopo l'applicazione di .gitignore."
}

$forbiddenNames = @()
$largeFiles = @()
$secretMatches = @()
$totalBytes = [int64]0
$textExtensions = @(
    '.css', '.env', '.example', '.html', '.ini', '.iss', '.js', '.json', '.md',
    '.mjs', '.ps1', '.py', '.spec', '.toml', '.ts', '.tsx', '.txt', '.yaml', '.yml'
)
$secretPatterns = @(
    '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'github_pat_[A-Za-z0-9_]{20,}',
    'gh[pousr]_[A-Za-z0-9]{20,}',
    'sk-(proj-)?[A-Za-z0-9_-]{20,}',
    'AKIA[0-9A-Z]{16}',
    'AIza[0-9A-Za-z_-]{30,}'
)

foreach ($relativePath in $trackedPaths) {
    $fullPath = Join-Path $projectRoot $relativePath
    if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        continue
    }

    $item = Get-Item -LiteralPath $fullPath
    $totalBytes += $item.Length
    $normalizedPath = $relativePath.Replace('\', '/')
    $leafName = [IO.Path]::GetFileName($relativePath)

    if (
        $leafName -eq '.env' -or
        $leafName -match '\.(pem|key|pfx|p12|keystore|jks)$' -or
        $normalizedPath -match '(^|/)(credentials|secrets?)(/|\.|$)'
    ) {
        $forbiddenNames += $relativePath
    }

    if ($item.Length -ge 95MB) {
        $largeFiles += "$relativePath ($([math]::Round($item.Length / 1MB, 2)) MB)"
    }

    $extension = $item.Extension.ToLowerInvariant()
    if ($item.Length -le 5MB -and ($textExtensions -contains $extension -or $leafName -like '.env*')) {
        $content = [IO.File]::ReadAllText($fullPath)
        foreach ($pattern in $secretPatterns) {
            if ($content -match $pattern) {
                $secretMatches += $relativePath
                break
            }
        }
    }
}

if ($forbiddenNames.Count -gt 0) {
    throw "File sensibili inclusi in Git:`n$($forbiddenNames -join "`n")"
}

if ($largeFiles.Count -gt 0) {
    throw "File oltre la soglia prudenziale di 95 MB:`n$($largeFiles -join "`n")"
}

if ($secretMatches.Count -gt 0) {
    throw "Possibili segreti rilevati nei file:`n$($secretMatches -join "`n")"
}

Write-Host ''
Write-Host "Controlli superati: $($trackedPaths.Count) file, $([math]::Round($totalBytes / 1MB, 2)) MB complessivi."
Write-Host 'File preparati per Git:'
& git status --short
Assert-GitSuccess -Action 'Lettura dello stato Git'

if (-not $Publish) {
    Write-Host ''
    Write-Host 'Anteprima completata: nessun repository remoto è stato creato e nessun push è stato eseguito.'
    Write-Host "Per pubblicare, ripeti il comando aggiungendo -Publish. Visibilità selezionata: $Visibility."
    exit 0
}

$ghCommand = Resolve-GitHubCli
& $ghCommand auth status
if ($LASTEXITCODE -ne 0) {
    throw 'GitHub CLI non è autenticata. Esegui prima: gh auth login'
}

$userName = (& git config user.name).Trim()
$userEmail = (& git config user.email).Trim()
if (-not $userName -or -not $userEmail) {
    throw 'Identità Git mancante. Configura git user.name e git user.email prima di pubblicare.'
}

if ($Visibility -eq 'public' -and -not (Test-Path -LiteralPath (Join-Path $projectRoot 'LICENSE'))) {
    Write-Warning 'Il repository sarà pubblico, ma il progetto non contiene ancora un file LICENSE.'
}

if (-not $Yes) {
    $confirmation = Read-Host "Scrivi PUBBLICA per creare/aggiornare '$Repository' come repository $Visibility e inviare i file"
    if ($confirmation -cne 'PUBBLICA') {
        throw 'Pubblicazione annullata.'
    }
}

& git diff --cached --quiet
$diffExitCode = $LASTEXITCODE
if ($diffExitCode -eq 1) {
    & git commit -m $CommitMessage
    Assert-GitSuccess -Action 'Creazione del commit'
} elseif ($diffExitCode -gt 1) {
    throw "Verifica delle modifiche Git non riuscita (codice $diffExitCode)."
}

& git branch -M main
Assert-GitSuccess -Action 'Impostazione del branch main'

$originUrl = (& git remote get-url origin 2>$null)
if ($LASTEXITCODE -ne 0) {
    $originUrl = $null
}

$repositoryName = ($Repository -split '/')[-1]
if ($originUrl) {
    if ($originUrl -notmatch "/$([regex]::Escape($repositoryName))(\.git)?$") {
        throw "Il remote origin esistente non corrisponde a '$Repository': $originUrl"
    }
    Write-Host "Remote origin esistente: $originUrl"
} else {
    & $ghCommand repo view $Repository --json url --jq '.url' *> $null
    if ($LASTEXITCODE -eq 0) {
        $existingUrl = (& $ghCommand repo view $Repository --json url --jq '.url').Trim()
        if ($LASTEXITCODE -ne 0 -or -not $existingUrl) {
            throw "Impossibile determinare l'URL del repository GitHub '$Repository'."
        }
        & git remote add origin "$existingUrl.git"
        Assert-GitSuccess -Action 'Aggiunta del remote origin'
    } else {
        $visibilityFlag = "--$Visibility"
        & $ghCommand repo create $Repository --source $projectRoot --remote origin $visibilityFlag --description $Description
        if ($LASTEXITCODE -ne 0) {
            throw "Creazione del repository GitHub '$Repository' non riuscita."
        }
    }
}

& git push --set-upstream origin main
Assert-GitSuccess -Action 'Push su GitHub'

$publishedUrl = (& $ghCommand repo view $Repository --json url --jq '.url').Trim()
Write-Host ''
Write-Host "Pubblicazione completata: $publishedUrl"
