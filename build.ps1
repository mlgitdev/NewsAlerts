# NewsAlerts Portable Build Automation Script
# Usage: .\build.ps1 [-Task <build|clean|run|check|help>]

param(
    [ValidateSet("build", "clean", "run", "run-app", "install-local", "installer", "check", "verify-packages", "wiki-sync", "worktree-new", "worktree-list", "worktree-remove", "worktree-merge", "worktree-prune", "issue-list", "issue-view", "help")]
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
$DistAppDir = Join-Path $ScriptDir "dist\NewsAlerts-App"
$DistAppExe = Join-Path $DistAppDir "NewsAlerts.exe"

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
    Write-Host "Build & Install Tasks:"
    Write-Host "  build             (default) Build portable executable and unpacked application folder" -ForegroundColor Yellow
    Write-Host "  run                         Launch the portable dist\NewsAlerts.exe" -ForegroundColor Yellow
    Write-Host "  run-app                     Launch the unpacked/installed dist\NewsAlerts-App\NewsAlerts.exe" -ForegroundColor Yellow
    Write-Host "  install-local               Install app into %LOCALAPPDATA%\Programs\NewsAlerts + shortcuts" -ForegroundColor Yellow
    Write-Host "  installer                   Compile Inno Setup Windows installer (requires ISCC)" -ForegroundColor Yellow
    Write-Host "  clean                       Remove build/ and dist/ artifacts and caches" -ForegroundColor Yellow
    Write-Host "  check                       Verify that secrets/ are excluded from the bundle" -ForegroundColor Yellow
    Write-Host "  verify-packages             Audit and verify standalone executable & release archives" -ForegroundColor Yellow
    Write-Host "  wiki-sync                   Synchronize docs/wiki/ documentation with GitHub Wiki" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Git Worktree Tasks:"
    Write-Host "  worktree-new    -Branch <b-name> [-Base <base>]   Create a new isolated worktree under .worktrees/" -ForegroundColor Yellow
    Write-Host "  worktree-list                                     List all active worktrees" -ForegroundColor Yellow
    Write-Host "  worktree-remove -Branch <b-name> [-Force]         Remove a worktree and prune metadata" -ForegroundColor Yellow
    Write-Host "  worktree-merge  -Branch <src> -Base <target>      Merge sub-branch back into target feat/ branch" -ForegroundColor Yellow
    Write-Host "  worktree-prune                                    Prune stale worktree references" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Issue Management Tasks (Issue-First Protocol):"
    Write-Host "  issue-list                                        List open repository issues via GitHub CLI" -ForegroundColor Yellow
    Write-Host "  issue-view      -Branch <issue-number>            Inspect specific issue details and discussion" -ForegroundColor Yellow
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
    $VersionFile = Join-Path $ScriptDir "VERSION"
    $appVer = "2.4.5"
    if (Test-Path $VersionFile) {
        $appVer = (Get-Content $VersionFile -Raw).Trim()
    } else {
        $VersionPy = Join-Path $ScriptDir "app\version.py"
        if (Test-Path $VersionPy) {
            $match = Select-String -Path $VersionPy -Pattern '__version__\s*=\s*["'']([^"'']+)["'']'
            if ($match) {
                $appVer = $match.Matches[0].Groups[1].Value
            }
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

    $sw = [System.Diagnostics.Stopwatch]::StartNew()

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

    Write-Host "[3/3] Verifying generated build artifacts..." -ForegroundColor Yellow
    if (-not (Test-Path $DistExe)) {
        Write-Error "Build finished but portable executable $DistExe was not found!"
        exit 1
    }
    if (-not (Test-Path $DistAppExe)) {
        Write-Error "Build finished but unpacked app $DistAppExe was not found!"
        exit 1
    }

    $itemExe = Get-Item $DistExe
    $sizeExeMB = [math]::Round($itemExe.Length / 1MB, 2)
    
    $appFiles = Get-ChildItem -Path $DistAppDir -Recurse | Measure-Object -Property Length -Sum
    $sizeAppMB = [math]::Round($appFiles.Sum / 1MB, 2)
    $sw.Stop()

    Write-Host ""
    Write-Host "[OK] Dual Build Successful!" -ForegroundColor Green
    Write-Host "     1. Portable: $DistExe ($sizeExeMB MB)" -ForegroundColor White
    Write-Host "     2. App Dir:  $DistAppDir ($sizeAppMB MB unpacked)" -ForegroundColor White
    Write-Host "     Duration:    $([math]::Round($sw.Elapsed.TotalSeconds, 1)) seconds" -ForegroundColor White
    Write-Host ""

    Verify-Secrets
}

function Run-Executable {
    if (-not (Test-Path $DistExe)) {
        Write-Host "[-] Portable executable not found at $DistExe. Building first..." -ForegroundColor Yellow
        Build-Executable
    }
    Write-Host ""
    Write-Host "[+] Launching portable $DistExe..." -ForegroundColor Cyan
    Start-Process -FilePath $DistExe
}

function Run-AppDirectory {
    if (-not (Test-Path $DistAppExe)) {
        Write-Host "[-] App directory executable not found at $DistAppExe. Building first..." -ForegroundColor Yellow
        Build-Executable
    }
    Write-Host ""
    Write-Host "[+] Launching unpacked app from $DistAppExe..." -ForegroundColor Cyan
    Start-Process -FilePath $DistAppExe
}

function Install-LocalApp {
    if (-not (Test-Path $DistAppDir)) {
        Write-Host "[-] App directory not found at $DistAppDir. Building first..." -ForegroundColor Yellow
        Build-Executable
    }

    $targetDir = Join-Path $env:LOCALAPPDATA "Programs\NewsAlerts"
    Write-Host ""
    Write-Host "[+] Installing NewsAlerts to $targetDir..." -ForegroundColor Cyan

    $running = Get-Process NewsAlerts -ErrorAction SilentlyContinue
    if ($running) {
        Write-Host "[-] Closing running NewsAlerts instance before installation..." -ForegroundColor Yellow
        $running | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 800
    }

    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }

    Copy-Item -Path "$DistAppDir\*" -Destination $targetDir -Recurse -Force
    $installedExe = Join-Path $targetDir "NewsAlerts.exe"

    # Create Desktop and Start Menu Shortcuts via WScript.Shell
    try {
        $wsh = New-Object -ComObject WScript.Shell
        
        # Desktop Shortcut
        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $deskShortcut = $wsh.CreateShortcut((Join-Path $desktopPath "NewsAlerts.lnk"))
        $deskShortcut.TargetPath = $installedExe
        $deskShortcut.WorkingDirectory = $targetDir
        $deskShortcut.IconLocation = "$installedExe,0"
        $deskShortcut.Description = "NewsAlerts Momentum Trading Terminal"
        $deskShortcut.Save()

        # Start Menu Shortcut
        $startMenuPath = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
        $smShortcut = $wsh.CreateShortcut((Join-Path $startMenuPath "NewsAlerts.lnk"))
        $smShortcut.TargetPath = $installedExe
        $smShortcut.WorkingDirectory = $targetDir
        $smShortcut.IconLocation = "$installedExe,0"
        $smShortcut.Description = "NewsAlerts Momentum Trading Terminal"
        $smShortcut.Save()

        Write-Host "[OK] Installed successfully to $targetDir" -ForegroundColor Green
        Write-Host "     Shortcuts created: Desktop and Start Menu" -ForegroundColor White
    } catch {
        Write-Host "[!] Note: Shortcuts could not be created automatically: $_" -ForegroundColor Yellow
    }
}

function Build-InnoInstaller {
    $isccPaths = @(
        (Get-Command "iscc" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source),
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )
    $iscc = $isccPaths | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

    if (-not $iscc) {
        Write-Host "[!] Inno Setup compiler (ISCC.exe) not found." -ForegroundColor Yellow
        Write-Host "    Install Inno Setup 6 (e.g. 'winget install JRSoftware.InnoSetup') to compile installers." -ForegroundColor DarkGray
        Write-Host "    The Inno script is ready at installer\NewsAlerts.iss" -ForegroundColor DarkGray
        return
    }

    if (-not (Test-Path $DistAppDir)) {
        Build-Executable
    }

    $issFile = Join-Path $ScriptDir "installer\NewsAlerts.iss"
    $appVer = (Get-Content (Join-Path $ScriptDir "VERSION") -Raw).Trim()
    Write-Host "[+] Compiling installer with Inno Setup: $iscc (v$appVer)..." -ForegroundColor Cyan
    & $iscc "/DMyAppVersion=$appVer" $issFile

    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Installer successfully built in dist\" -ForegroundColor Green
    } else {
        Write-Error "Inno Setup compilation failed with code $LASTEXITCODE."
    }
}

$WorktreeScript = Join-Path $ScriptDir "scripts\worktree.ps1"
if (-not (Test-Path $WorktreeScript)) {
    # If in worktree, check repo root
    $WorktreeScript = Join-Path $ScriptDir "..\..\scripts\worktree.ps1"
}

function Get-GhCli {
    $cmd = Get-Command "gh" -ErrorAction SilentlyContinue
    if ($cmd) { return "gh" }
    $defPath = "C:\Program Files\GitHub CLI\gh.exe"
    if (Test-Path $defPath) { return $defPath }
    return $null
}

if ($Task -eq "build") {
    Build-Executable
} elseif ($Task -eq "clean") {
    Clean-Artifacts
} elseif ($Task -eq "run") {
    Run-Executable
} elseif ($Task -eq "run-app") {
    Run-AppDirectory
} elseif ($Task -eq "install-local") {
    Install-LocalApp
} elseif ($Task -eq "installer") {
    Build-InnoInstaller
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
} elseif ($Task -eq "wiki-sync") {
    $SyncScript = Join-Path $ScriptDir "scripts\sync_wiki.py"
    if (-not (Test-Path $SyncScript)) {
        $SyncScript = Join-Path $ScriptDir "..\..\scripts\sync_wiki.py"
    }
    & $VenvPython $SyncScript
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
} elseif ($Task -eq "issue-list") {
    $gh = Get-GhCli
    if ($gh) {
        & $gh issue list --state open
    } else {
        Write-Error "GitHub CLI (gh) was not found in PATH or standard installation directory."
    }
} elseif ($Task -eq "issue-view") {
    $gh = Get-GhCli
    if ($gh) {
        if (-not $Branch) {
            Write-Host "Usage: .\build.ps1 -Task issue-view -Branch <issue-number>" -ForegroundColor Yellow
        } else {
            & $gh issue view $Branch
        }
    } else {
        Write-Error "GitHub CLI (gh) was not found in PATH or standard installation directory."
    }
} elseif ($Task -eq "help") {
    Show-Help
} else {
    Show-Help
}
