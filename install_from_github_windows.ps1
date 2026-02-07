param(
    [string]$RepoUrl = "",
    [string]$InstallDir = "$env:USERPROFILE\CanvasQuizBuilder"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git is required but not found in PATH."
}

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' is required but not found in PATH."
}

$detectedRepoUrl = $null
try {
    if ($PSScriptRoot) {
        $detectedRepoUrl = git -C $PSScriptRoot remote get-url origin 2>$null
    }
}
catch {
    $detectedRepoUrl = $null
}

if ([string]::IsNullOrWhiteSpace($RepoUrl)) {
    if (-not [string]::IsNullOrWhiteSpace($detectedRepoUrl)) {
        $RepoUrl = $detectedRepoUrl
    } else {
        $RepoUrl = "https://github.com/staffordlumsden/CanvasQuizMaker.git"
    }
}

Write-Host "Installing Canvas Quiz Builder"
Write-Host "Repo: $RepoUrl"
Write-Host "Install dir: $InstallDir"

$parent = Split-Path -Parent $InstallDir
if (-not (Test-Path $parent)) {
    New-Item -ItemType Directory -Path $parent | Out-Null
}

if (Test-Path "$InstallDir\.git") {
    $installedRemoteUrl = $null
    try {
        $installedRemoteUrl = git -C $InstallDir remote get-url origin 2>$null
    }
    catch {
        $installedRemoteUrl = $null
    }
    if ($installedRemoteUrl -and ($installedRemoteUrl -ne $RepoUrl)) {
        throw "Existing install at $InstallDir points to a different repo: $installedRemoteUrl. Remove it or choose a different -InstallDir."
    }
    Write-Host "Existing clone found. Pulling latest changes..."
    git -C $InstallDir pull --ff-only
} elseif (Test-Path $InstallDir) {
    throw "$InstallDir exists but is not a git repository."
} else {
    Write-Host "Cloning repository..."
    git clone $RepoUrl $InstallDir
}

Push-Location $InstallDir
try {
    if (-not (Test-Path ".venv")) {
        Write-Host "Creating virtual environment..."
        py -3 -m venv .venv
    }

    Write-Host "Installing dependencies..."
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\python.exe -m pip install .

    if (-not (Test-Path ".\run_text2qti_web.bat")) {
        throw "run_text2qti_web.bat not found in repository."
    }
}
finally {
    Pop-Location
}

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Canvas Quiz Builder.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "cmd.exe"
$shortcut.Arguments = "/c `"$InstallDir\run_text2qti_web.bat`""
$shortcut.WorkingDirectory = $InstallDir
$shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
$shortcut.Save()

Write-Host ""
Write-Host "Install complete."
Write-Host "Desktop shortcut created: $shortcutPath"
Write-Host "Double-click it to start the app."
