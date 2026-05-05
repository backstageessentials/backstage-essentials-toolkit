#Requires -Version 5.1
<#
.SYNOPSIS
    Backstage Essentials Toolkit installer for Windows.

.DESCRIPTION
    Verifies prerequisites (Python 3.10+, git, npm, Claude Code), clones the
    toolkit to %USERPROFILE%\Code\backstage-essentials-toolkit, runs
    pip install -e ., and verifies the bes CLI works.

    Idempotent: re-running on a configured machine pulls the latest and
    re-verifies prerequisites.

.PARAMETER InstallParent
    Override the parent directory the toolkit is cloned into.
    Default: $env:USERPROFILE\Code

.EXAMPLE
    Invoke-WebRequest -UseBasicParsing https://raw.githubusercontent.com/backstageessentials/backstage-essentials-toolkit/main/install.ps1 | Invoke-Expression

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\install.ps1

.NOTES
    If PowerShell refuses to run this script, you have two options:
      1. One-shot:    powershell -ExecutionPolicy Bypass -File .\install.ps1
      2. Permanent:   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
                      (then re-run the script)
#>

[CmdletBinding()]
param(
    [string]$InstallParent = (Join-Path $env:USERPROFILE 'Code')
)

$ErrorActionPreference = 'Stop'

$RepoUrl     = 'https://github.com/backstageessentials/backstage-essentials-toolkit.git'
$InstallDir  = Join-Path $InstallParent 'backstage-essentials-toolkit'
$MinPyMajor  = 3
$MinPyMinor  = 10

# ---- output helpers --------------------------------------------------------

function Write-Step([string]$Text) {
    Write-Host ""
    Write-Host "==> " -ForegroundColor Blue -NoNewline
    Write-Host $Text -ForegroundColor White
}
function Write-Ok    ([string]$Text) { Write-Host "    OK     " -ForegroundColor Green   -NoNewline; Write-Host $Text }
function Write-Info  ([string]$Text) { Write-Host "    info   " -ForegroundColor DarkGray -NoNewline; Write-Host $Text }
function Write-Warn2 ([string]$Text) { Write-Host "    warn   " -ForegroundColor Yellow  -NoNewline; Write-Host $Text }
function Write-Fail  ([string]$Text) { Write-Host "    error  " -ForegroundColor Red     -NoNewline; Write-Host $Text }

function Stop-Install([string]$Text) {
    Write-Fail $Text
    Write-Host ""
    Write-Host "Installation stopped." -ForegroundColor Red -NoNewline
    Write-Host " Fix the issue above and re-run."
    exit 1
}

# ---- prerequisite checks ---------------------------------------------------

function Get-WorkingPython {
    # Returns the path of the first python on PATH whose version is >= MinPy.
    $candidates = @('python', 'python3', 'py')
    foreach ($exe in $candidates) {
        $cmd = Get-Command $exe -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }

        # py launcher needs -3 to pick Python 3
        $argList = @('-c', 'import sys; print("{}.{}.{}".format(*sys.version_info[:3]))')
        if ($exe -eq 'py') { $argList = @('-3') + $argList }

        try {
            $verStr = & $cmd.Source @argList 2>$null
            if (-not $verStr) { continue }
            $parts = $verStr.Trim().Split('.')
            $maj = [int]$parts[0]; $min = [int]$parts[1]
            if (($maj -gt $MinPyMajor) -or ($maj -eq $MinPyMajor -and $min -ge $MinPyMinor)) {
                return [pscustomobject]@{ Path = $cmd.Source; Version = $verStr.Trim(); UsesPyLauncher = ($exe -eq 'py') }
            }
        } catch {}
    }
    return $null
}

function Require-Python {
    $py = Get-WorkingPython
    if ($py) {
        Write-Ok "Python $($py.Version) at $($py.Path)"
        $script:PythonPath = $py.Path
        $script:PythonUsesLauncher = $py.UsesPyLauncher
        return
    }
    Write-Fail "Python $MinPyMajor.$MinPyMinor+ not found."
    Write-Info "Download the official installer:  https://www.python.org/downloads/windows/"
    Write-Info "When installing, check 'Add Python to PATH' on the first installer screen."
    Stop-Install "Install Python and re-run this script."
}

function Require-Command {
    param([string]$Cmd, [string]$Hint)
    $found = Get-Command $Cmd -ErrorAction SilentlyContinue
    if ($found) {
        Write-Ok "$Cmd at $($found.Source)"
        return
    }
    Write-Fail "$Cmd not found."
    Write-Info $Hint
    Stop-Install "Install $Cmd and re-run this script."
}

function Require-ClaudeCode {
    $found = Get-Command 'claude' -ErrorAction SilentlyContinue
    if ($found) {
        $v = (& $found.Source --version 2>$null | Select-Object -First 1)
        Write-Ok "Claude Code: $v"
        return
    }
    Write-Fail "Claude Code (the 'claude' CLI) is not installed."
    Write-Info "The toolkit drives Claude Code to author lessons, quizzes, and diagrams."
    Write-Info "Install it before continuing:"
    Write-Info "  npm install -g @anthropic-ai/claude-code"
    Write-Info "Or follow Anthropic's instructions:  https://docs.anthropic.com/en/docs/claude-code"
    Stop-Install "Install Claude Code and re-run this script."
}

# ---- pip install -----------------------------------------------------------

function Invoke-PipInstall {
    param([string]$Target)
    Push-Location $Target
    try {
        $pyArgs = @()
        if ($script:PythonUsesLauncher) { $pyArgs += '-3' }
        $pyArgs += @('-m', 'pip', 'install', '-e', '.')

        $output = & $script:PythonPath @pyArgs 2>&1
        $output | Tee-Object -FilePath "$env:TEMP\bes_pip.log" | Out-Host
        if ($LASTEXITCODE -eq 0) { return $true }

        if ($output -match 'externally-managed-environment') {
            Write-Warn2 "Python flagged this environment as externally-managed (PEP 668). Retrying with --user..."
            $pyArgs2 = @()
            if ($script:PythonUsesLauncher) { $pyArgs2 += '-3' }
            $pyArgs2 += @('-m', 'pip', 'install', '--user', '-e', '.')
            $output2 = & $script:PythonPath @pyArgs2 2>&1
            $output2 | Tee-Object -FilePath "$env:TEMP\bes_pip.log" | Out-Host
            if ($LASTEXITCODE -eq 0) {
                $script:UsedUserInstall = $true
                return $true
            }
        }
        return $false
    } finally {
        Pop-Location
    }
}

# ---- main ------------------------------------------------------------------

Write-Host "Backstage Essentials Toolkit installer" -ForegroundColor White
Write-Host "https://github.com/backstageessentials/backstage-essentials-toolkit" -ForegroundColor DarkGray

Write-Step "1/6  Detecting OS"
$arch = $env:PROCESSOR_ARCHITECTURE
Write-Ok "Windows ($arch)"

Write-Step "2/6  Checking prerequisites"
Require-Python
Require-Command 'git' "Download Git for Windows: https://git-scm.com/download/win   (accept defaults during install)"
Require-Command 'npm' "Install Node.js LTS:        https://nodejs.org/en/download   (npm comes with Node)"
Require-ClaudeCode

Write-Step "3/6  Preparing install directory"
if (-not (Test-Path $InstallParent)) {
    New-Item -ItemType Directory -Path $InstallParent -Force | Out-Null
    Write-Ok "Created $InstallParent"
} else {
    Write-Ok "$InstallParent exists"
}

Write-Step "4/6  Cloning or updating toolkit"
if (Test-Path (Join-Path $InstallDir '.git')) {
    Write-Info "Existing checkout found at $InstallDir. Pulling latest..."
    try {
        & git -C $InstallDir pull --ff-only | Out-Host
        if ($LASTEXITCODE -ne 0) { throw "git pull exited $LASTEXITCODE" }
        Write-Ok "Updated $InstallDir"
    } catch {
        Write-Warn2 "git pull did not fast-forward. Leaving the checkout as-is."
        Write-Info "If you have local changes, commit or stash them and re-run this script."
    }
} elseif (Test-Path $InstallDir) {
    Stop-Install "$InstallDir exists but is not a git checkout. Move or remove it and re-run."
} else {
    try {
        & git clone $RepoUrl $InstallDir | Out-Host
        if ($LASTEXITCODE -ne 0) { throw "git clone exited $LASTEXITCODE" }
        Write-Ok "Cloned to $InstallDir"
    } catch {
        Stop-Install "git clone failed. Check your network and that $RepoUrl is reachable."
    }
}

Write-Step "5/6  Installing the bes CLI (pip install -e .)"
$script:UsedUserInstall = $false
if (Invoke-PipInstall -Target $InstallDir) {
    Write-Ok "Installed editable package"
} else {
    Write-Fail "pip install failed. See $env:TEMP\bes_pip.log for the full output."
    Write-Info "Common fixes:"
    Write-Info "  - Upgrade pip:  $script:PythonPath -m pip install --upgrade pip"
    Write-Info "  - Re-open PowerShell to refresh the PATH, then re-run."
    Stop-Install "Could not install the bes CLI."
}

Write-Step "6/6  Verifying installation"
$bes = Get-Command 'bes' -ErrorAction SilentlyContinue
if ($bes) {
    $besVer = (& $bes.Source --version 2>$null)
    Write-Ok "$besVer"
} elseif ($script:UsedUserInstall) {
    $userBase = & $script:PythonPath -m site --user-base
    $userScripts = Join-Path $userBase.Trim() 'Scripts'
    Write-Fail "bes installed but is not on your PATH."
    Write-Info "Add this folder to your PATH (System Properties > Environment Variables > Path):"
    Write-Info "  $userScripts"
    Write-Info "Then close and reopen PowerShell."
    exit 2
} else {
    Write-Fail "bes installed but the shell cannot find it. Close and reopen PowerShell, then run:  bes --version"
    exit 2
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green -NoNewline
Write-Host " Toolkit is ready at $InstallDir"
Write-Host ""
Write-Host "Next step - start your first course:"
Write-Host ""
Write-Host "    cd $InstallParent"
Write-Host "    bes new-course"
Write-Host ""
Write-Host "Then open the new course folder in Claude Code and follow the prompts." -ForegroundColor DarkGray
