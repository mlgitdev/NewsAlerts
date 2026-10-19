# NewsAlerts Portable Build Automation Script
# Usage: .\build.ps1 [-Task <build|clean|run|check|help>]

param(
    [ValidateSet("build", "clean", "run", "check", "verify-packages", "worktree-new", "worktree-list", "worktree-remove", "worktree-merge", "worktree-prune", "help")]
    [string]$Task = "build",

    [string]$Branch = "",
    [string]$Base = "main",
    [switch]$Force
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"
$VenvPyInstaller = Join-Path $ScriptDir ".venv\Scripts\pyinstaller.exe"
$DistExe = Join-Path $ScriptDir "dist\NewsAlerts.exe"

# If running inside a .worktrees subdirectory, inherit parent .venv
if (-not (Test-Path $VenvPython)) {
    $ParentVenv = Join-Path $ScriptDir "..\..\.venv\Scripts\python.exe"
    if (Test-Path $ParentVenv) {
        $VenvPython = (Resolve-Path $ParentVenv).Path
        $VenvPyInstaller = (Resolve-Path (Join-Path $ScriptDir "..\..\.venv\Scripts\pyinstaller.exe")).Path
        Write-Host "[+] Inherited shared virtual environment from repository root: $VenvPython" -ForegroundColor DarkGray
    }
}

function Show-Help {
    Write-Host ""
    Write-Host "NewsAlerts Build & Worktree Automation" -ForegroundColor Cyan
    Write-Host "=====================================" -ForegroundColor Cyan
    Write-Host "Usage: .\build.ps1 [-Task <Task>] [-Branch <branch>] [-Base <base>]"
    Write-Host ""
    Write-Host "Build Tasks:"
    Write-Host "  build             (default) Build portable NewsAlerts.exe standalone executable" -ForegroundColor Yellow
    Write-Host "  clean                       Remove build/ and dist/ artifacts and caches" -ForegroundColor Yellow
    Write-Host "  run                         Launch the built dist\NewsAlerts.exe" -ForegroundColor Yellow
    Write-Host "  check                       Verify that secrets/ are excluded from the bundle" -ForegroundColor Yellow
    Write-Host "  verify-packages             Audit and verify standalone executable & release archives" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Git Worktree Tasks:"
    Write-Host "  worktree-new    -Branch <b-name> [-Base <base>]   Create a new isolated worktree under .worktrees/" -ForegroundColor Yellow
    Write-Host "  worktree-list                                     List all active worktrees" -ForegroundColor Yellow
    Write-Host "  worktree-remove -Branch <b-name> [-Force]         Remove a worktree and prune metadata" -ForegroundColor Yellow
    Write-Host "  worktree-merge  -Branch <src> -Base <target>      Merge sub-branch back into target feat/ branch" -ForegroundColor Yellow
    Write-Host "  worktree-prune                                    Prune stale worktree references" -ForegroundColor Yellow
    Write-Host "  help                                              Show this help message" -ForegroundColor Yellow
    Write-Host ""
}

function Ensure-Environment {
    if (-not (Test-Path $VenvPython)) {
        Write-Host "[-] Virtual environment not found. Creating .venv..." -ForegroundColor Yellow
        python -m venv (Join-Path $ScriptDir ".venv")
        if (-not (Test-Path $VenvPython)) {
            Write-Error "Failed to create virtual environment."
            exit 1
        }
    }

    if (-not (Test-Path $VenvPyInstaller)) {
        Write-Host "[-] Installing build dependencies from requirements.txt..." -ForegroundColor Yellow
        & $VenvPython -m pip install --upgrade pip
        & $VenvPython -m pip install -r (Join-Path $ScriptDir "requirements.txt")
    }
}

function Clean-Artifacts {
    Write-Host ""
    Write-Host "[+] Cleaning build artifacts..." -ForegroundColor Cyan
    $pathsToClean = @(
        (Join-Path $ScriptDir "build"),
        (Join-Path $ScriptDir "dist"),
        (Join-Path $ScriptDir "__pycache__"),
        (Join-Path $ScriptDir "app\__pycache__")
    )
    foreach ($p in $pathsToClean) {
        if (Test-Path $p) {
            Write-Host "    Removing: $p" -ForegroundColor DarkGray
            Remove-Item -Path $p -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "[OK] Clean complete." -ForegroundColor Green
    Write-Host ""
}

function Verify-Secrets {
    Write-Host "[*] Auditing bundle for secrets leakage..." -ForegroundColor Cyan
    $pkgFile = Join-Path $ScriptDir "build\NewsAlerts\PKG-00.toc"
    if (Test-Path $pkgFile) {
        $content = Get-Content $pkgFile -Raw
        if ($content.Contains("keys.toml") -or $content.Contains("secrets\keys.toml")) {
            Write-Host "[!] WARNING: Secret file detected in build archive!" -ForegroundColor Red
        } else {
            Write-Host "[OK] Security check passed: No secrets/ or keys.toml in build bundle." -ForegroundColor Green
        }
    } else {
        Write-Host "[!] Note: build\NewsAlerts\PKG-00.toc not found (run build first)." -ForegroundColor Yellow
    }
}

function Build-Executable {
    $VersionPy = Join-Path $ScriptDir "app\version.py"
    $appVer = "2.4.0"
    if (Test-Path $VersionPy) {
        $match = Select-String -Path $VersionPy -Pattern '__version__\s*=\s*["'']([^"'']+)["'']'
        if ($match) {
            $appVer = $match.Matches[0].Groups[1].Value
        }
    }

    Write-Host ""
    Write-Host "=======================================================" -ForegroundColor Cyan
    Write-Host " Building Portable Executable: NewsAlerts.exe (v$appVer)" -ForegroundColor Cyan
    Write-Host " Target OS: Windows x64 | SemVer 2.0.0: v$appVer" -ForegroundColor Cyan
    Write-Host " Secrets: Excluded (configured via AppData / Settings UI)" -ForegroundColor Cyan
    Write-Host "=======================================================" -ForegroundColor Cyan
    Write-Host ""

    Ensure-Environment

    $running = Get-Process NewsAlerts -ErrorAction SilentlyContinue
    if ($running) {
        Write-Host "[-] Closing running NewsAlerts instance before build..." -ForegroundColor Yellow
        $running | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 800
    }

    Write-Host "[1/3] Verifying dependencies and web assets..." -ForegroundColor Yellow
    $webIndex = Join-Path $ScriptDir "web\index.html"
    if (-not (Test-Path $webIndex)) {
        Write-Error "Web assets not found at $webIndex!"
        exit 1
    }

    Write-Host "[2/3] Running PyInstaller with NewsAlerts.spec..." -ForegroundColor Yellow
    $specFile = Join-Path $ScriptDir "NewsAlerts.spec"
    & $VenvPyInstaller $specFile --clean --noconfirm

    if ($LASTEXITCODE -ne 0) {
        Write-Error "PyInstaller build failed with exit code $LASTEXITCODE."
        exit $LASTEXITCODE
    }

    Write-Host "[3/3] Verifying generated executable..." -ForegroundColor Yellow
    if (-not (Test-Path $DistExe)) {
        Write-Error "Build finished but $DistExe was not found!"
        exit 1
    }

    $item = Get-Item $DistExe
    $sizeMB = [math]::Round($item.Length / 1MB, 2)
    $sw.Stop()

    Write-Host ""
    Write-Host "[OK] Build Successful!" -ForegroundColor Green
    Write-Host "     Output:   $DistExe" -ForegroundColor White
    Write-Host "     Size:     $sizeMB MB" -ForegroundColor White
    Write-Host "     Duration: $([math]::Round($sw.Elapsed.TotalSeconds, 1)) seconds" -ForegroundColor White
    Write-Host ""

    Verify-Secrets
}

function Run-Executable {
    if (-not (Test-Path $DistExe)) {
        Write-Host "[-] Executable not found at $DistExe. Building first..." -ForegroundColor Yellow
        Build-Executable
    }
    Write-Host ""
    Write-Host "[+] Launching $DistExe..." -ForegroundColor Cyan
    Start-Process -FilePath $DistExe
}

$WorktreeScript = Join-Path $ScriptDir "scripts\worktree.ps1"
if (-not (Test-Path $WorktreeScript)) {
    # If in worktree, check repo root
    $WorktreeScript = Join-Path $ScriptDir "..\..\scripts\worktree.ps1"
}

if ($Task -eq "build") {
    Build-Executable
} elseif ($Task -eq "clean") {
    Clean-Artifacts
} elseif ($Task -eq "run") {
    Run-Executable
} elseif ($Task -eq "check") {
    Verify-Secrets
} elseif ($Task -eq "verify-packages") {
    $VerifyScript = Join-Path $ScriptDir "scripts\verify-packages.py"
    if (-not (Test-Path $VerifyScript)) {
        $VerifyScript = Join-Path $ScriptDir "..\..\scripts\verify-packages.py"
    }
    $targetExe = $DistExe
    if (-not (Test-Path $targetExe)) {
        $parentExe = Join-Path $ScriptDir "..\..\dist\NewsAlerts.exe"
        if (Test-Path $parentExe) {
            $targetExe = $parentExe
        }
    }
    & $VenvPython $VerifyScript --exe $targetExe
} elseif ($Task -eq "worktree-new") {
    & $WorktreeScript new $Branch $Base
} elseif ($Task -eq "worktree-list") {
    & $WorktreeScript list
} elseif ($Task -eq "worktree-remove") {
    if ($Force) {
        & $WorktreeScript remove $Branch -Force
    } else {
        & $WorktreeScript remove $Branch
    }
} elseif ($Task -eq "worktree-merge") {
    & $WorktreeScript merge-back $Branch $Base
} elseif ($Task -eq "worktree-prune") {
    & $WorktreeScript prune
} elseif ($Task -eq "help") {
    Show-Help
} else {
    Show-Help
}
