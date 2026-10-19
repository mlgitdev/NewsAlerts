# NewsAlerts Git Worktree Automation for PowerShell
# Usage:
#   .\scripts\worktree.ps1 new <branch-name> [base-branch]
#   .\scripts\worktree.ps1 list
#   .\scripts\worktree.ps1 remove <branch-or-folder> [-Force]
#   .\scripts\worktree.ps1 merge-back <source-branch> [target-branch]

param(
    [Parameter(Position = 0)]
    [ValidateSet("new", "list", "remove", "merge-back", "prune", "help")]
    [string]$Action = "help",

    [Parameter(Position = 1)]
    [string]$Branch = "",

    [Parameter(Position = 2)]
    [string]$Base = "main",

    [switch]$Force
)

$GitCommonDir = (git rev-parse --git-common-dir 2>$null)
if (-not $GitCommonDir) {
    Write-Error "Not inside a git repository."
    exit 1
}
$RepoRoot = (Resolve-Path (Join-Path $GitCommonDir "..")).Path

# Ensure we operate relative to the repository root
$WorktreesDir = Join-Path $RepoRoot ".worktrees"

function Show-Usage {
    Write-Host ""
    Write-Host "NewsAlerts Git Worktree Helper" -ForegroundColor Cyan
    Write-Host "=============================" -ForegroundColor Cyan
    Write-Host "Manages isolated development worktrees without dirtying the main repository root."
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  .\scripts\worktree.ps1 new <branch-name> [base-branch]       Create a new worktree under .worktrees/" -ForegroundColor Yellow
    Write-Host "  .\scripts\worktree.ps1 list                                  List all active worktrees" -ForegroundColor Yellow
    Write-Host "  .\scripts\worktree.ps1 remove <branch-or-folder> [-Force]    Safely remove a worktree" -ForegroundColor Yellow
    Write-Host "  .\scripts\worktree.ps1 merge-back <source> [target]          Merge sub-branch back into target feat/ branch" -ForegroundColor Yellow
    Write-Host "  .\scripts\worktree.ps1 prune                                 Prune deleted worktree references" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Naming Conventions:"
    Write-Host "  Features:    feat/<short-descriptor>   (e.g. feat/vwap-filter)" -ForegroundColor DarkGray
    Write-Host "  Bug Fixes:   fix/<short-descriptor>    (e.g. fix/tape-timestamp)" -ForegroundColor DarkGray
    Write-Host "  Major Epics: major/<short-descriptor>  (e.g. major/v3-redesign)" -ForegroundColor DarkGray
    Write-Host "  Sub-tasks:   sub/<feature>/<task>      (e.g. sub/vwap-filter/tests)" -ForegroundColor DarkGray
    Write-Host ""
}

function Sanitize-BranchPath([string]$b) {
    # Replace slashes and invalid characters with hyphens
    $clean = $b -replace "[/\\:]", "-"
    $clean = $clean -replace "[^a-zA-Z0-9_\.\-]", ""
    return $clean
}

function New-Worktree {
    if (-not $Branch) {
        Write-Error "Missing required branch-name. Example: .\scripts\worktree.ps1 new feat/vwap-filter"
        exit 1
    }

    # Validate branch name prefix
    $validPrefixes = @("feat/", "fix/", "major/", "docs/", "perf/", "refactor/", "test/", "chore/", "sub/")
    $hasValidPrefix = $false
    foreach ($p in $validPrefixes) {
        if ($Branch.StartsWith($p)) {
            $hasValidPrefix = $true
            break
        }
    }

    if (-not $hasValidPrefix) {
        Write-Host "[!] Warning: Branch '$Branch' does not start with standard prefix (feat/, fix/, major/, sub/)." -ForegroundColor Yellow
    }

    $folderName = Sanitize-BranchPath $Branch
    $targetPath = Join-Path $WorktreesDir $folderName

    if (Test-Path $targetPath) {
        Write-Error "Worktree directory already exists: $targetPath"
        exit 1
    }

    if (-not (Test-Path $WorktreesDir)) {
        New-Item -ItemType Directory -Path $WorktreesDir -Force | Out-Null
    }

    # Check if branch already exists in git
    $branchExists = (git branch --list $Branch)
    if ($branchExists) {
        Write-Host "[+] Adding worktree for existing branch '$Branch' at $targetPath..." -ForegroundColor Cyan
        git worktree add $targetPath $Branch
    } else {
        Write-Host "[+] Creating new branch '$Branch' from '$Base' in worktree at $targetPath..." -ForegroundColor Cyan
        git worktree add -b $Branch $targetPath $Base
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create git worktree."
        exit $LASTEXITCODE
    }

    Write-Host ""
    Write-Host "Worktree ready!" -ForegroundColor Green
    Write-Host "Location: $targetPath" -ForegroundColor White
    Write-Host "Branch:   $Branch" -ForegroundColor White
    Write-Host ""
    Write-Host "To start working in this worktree:"
    Write-Host "  cd $targetPath" -ForegroundColor Yellow
    Write-Host ""
}

function List-Worktrees {
    Write-Host ""
    Write-Host "Active Git Worktrees:" -ForegroundColor Cyan
    git worktree list
    Write-Host ""
}

function Remove-Worktree {
    if (-not $Branch) {
        Write-Error "Missing required branch or folder name. Example: .\scripts\worktree.ps1 remove feat-vwap-filter"
        exit 1
    }

    $folderName = Sanitize-BranchPath $Branch
    $targetPath = Join-Path $WorktreesDir $folderName

    # If user provided direct folder name that exists
    if (-not (Test-Path $targetPath)) {
        $candidate = Join-Path $WorktreesDir $Branch
        if (Test-Path $candidate) {
            $targetPath = $candidate
        }
    }

    if (-not (Test-Path $targetPath)) {
        Write-Error "Worktree path not found: $targetPath"
        exit 1
    }

    Write-Host "[+] Removing worktree at $targetPath..." -ForegroundColor Yellow
    if ($Force) {
        git worktree remove --force $targetPath
    } else {
        git worktree remove $targetPath
    }

    git worktree prune
    Write-Host "[OK] Worktree removed and pruned successfully." -ForegroundColor Green
}

function Merge-Back {
    if (-not $Branch) {
        Write-Error "Missing required source branch. Example: .\scripts\worktree.ps1 merge-back sub/vwap/tests feat/vwap-filter"
        exit 1
    }

    $source = $Branch
    $target = if ($Base -ne "main") { $Base } else {
        Write-Error "Please specify the target branch to merge into. Example: .\scripts\worktree.ps1 merge-back $source feat/my-parent-feature"
        exit 1
    }

    Write-Host "[+] Merging sub-branch '$source' into target '$target'..." -ForegroundColor Cyan
    git checkout $target
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Could not checkout target branch '$target'."
        exit 1
    }

    git merge --no-ff $source -m "feat(worktree): merge $source into $target"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Successfully merged $source into $target." -ForegroundColor Green
        Write-Host "You can now push '$target' or open a PR." -ForegroundColor Yellow
    } else {
        Write-Error "Merge conflicts detected. Please resolve conflicts in $target."
    }
}

switch ($Action) {
    "new"        { New-Worktree }
    "list"       { List-Worktrees }
    "remove"     { Remove-Worktree }
    "merge-back" { Merge-Back }
    "prune"      { git worktree prune; Write-Host "[OK] Worktree list pruned." -ForegroundColor Green }
    default      { Show-Usage }
}
