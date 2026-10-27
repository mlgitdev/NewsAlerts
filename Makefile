# -----------------------------------------------------------------------------
# NewsAlerts Universal Cross-Platform Makefile
# Compatible with Windows (GNU Make / ezwinports / winget), Linux, and macOS
# -----------------------------------------------------------------------------

.PHONY: all env env-win env-linux env-mac build run run-app install-local installer test verify check clean worktree-list worktree-new wiki-sync help

# Platform Detection
ifeq ($(OS),Windows_NT)
    PLATFORM := Windows
    POWERSHELL := powershell -NoProfile -ExecutionPolicy Bypass

    ifeq ($(wildcard .venv/Scripts/python.exe),)
        ifeq ($(wildcard ../../.venv/Scripts/python.exe),)
            PYTHON := python
        else
            PYTHON := ../../.venv/Scripts/python.exe
        endif
    else
        PYTHON := .venv/Scripts/python.exe
    endif

    CMD_ENV           := $(POWERSHELL) -File ./build.ps1 -Task env
    CMD_BUILD         := $(POWERSHELL) -File ./build.ps1 -Task build
    CMD_RUN           := $(POWERSHELL) -File ./build.ps1 -Task run
    CMD_RUN_APP       := $(POWERSHELL) -File ./build.ps1 -Task run-app
    CMD_INSTALL_LOCAL := $(POWERSHELL) -File ./build.ps1 -Task install-local
    CMD_INSTALLER     := $(POWERSHELL) -File ./build.ps1 -Task installer
    CMD_CLEAN         := $(POWERSHELL) -File ./build.ps1 -Task clean
    CMD_CHECK         := $(POWERSHELL) -File ./build.ps1 -Task check
    CMD_VERIFY        := $(POWERSHELL) -File ./build.ps1 -Task verify-packages
    CMD_WIKI_SYNC     := $(POWERSHELL) -File ./build.ps1 -Task wiki-sync
    CMD_TEST          := $(PYTHON) -m unittest discover -s tests -p "test_*.py"
    CMD_WT_LIST       := $(POWERSHELL) -File ./build.ps1 -Task worktree-list
    CMD_WT_NEW        := $(POWERSHELL) -File ./build.ps1 -Task worktree-new -Branch "$(BRANCH)" -Base "$(BASE)"
    CMD_ISSUE_LIST    := $(POWERSHELL) -File ./build.ps1 -Task issue-list
    CMD_ISSUE_VIEW    := $(POWERSHELL) -File ./build.ps1 -Task issue-view -Branch "$(ISSUE)"
else
    UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Darwin)
        PLATFORM := macOS
    else
        PLATFORM := Linux
    endif

    ifeq ($(wildcard .venv/bin/python),)
        ifeq ($(wildcard ../../.venv/bin/python),)
            PYTHON := python3
        else
            PYTHON := ../../.venv/bin/python
        endif
    else
        PYTHON := .venv/bin/python
    endif

    CMD_ENV           := test -d .venv || $(PYTHON) -m venv .venv; .venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements.txt
    CMD_BUILD         := $(PYTHON) -m PyInstaller --clean -y NewsAlerts.spec
    CMD_RUN           := ./run.sh
    CMD_RUN_APP       := ./run.sh
    CMD_INSTALL_LOCAL := mkdir -p ~/.local/share/NewsAlerts && cp -r . ~/.local/share/NewsAlerts/
    CMD_INSTALLER     := echo "[!] Inno Setup Windows installer is only compiled on Windows or CI runners."
    CMD_CLEAN         := rm -rf build/ dist/ .venv/ .pytest_cache/ __pycache__/ app/__pycache__/ tests/__pycache__/ *.spec.bak
    CMD_CHECK         := git diff --staged --name-only | grep -E "keys|secret|token|\.env" && exit 1 || echo "[OK] No secrets found in staged files."
    CMD_VERIFY        := $(PYTHON) scripts/verify-packages.py
    CMD_WIKI_SYNC     := $(PYTHON) scripts/sync_wiki.py
    CMD_TEST          := $(PYTHON) -m unittest discover -s tests -p "test_*.py"
    CMD_WT_LIST       := ./scripts/worktree.sh list
    CMD_WT_NEW        := ./scripts/worktree.sh new "$(BRANCH)" "$(BASE)"
    CMD_ISSUE_LIST    := gh issue list --state open
    CMD_ISSUE_VIEW    := gh issue view "$(ISSUE)"
endif


BRANCH ?=
BASE ?= main
ISSUE ?=

all: help

env:
	@echo "[*] [$(PLATFORM)] Preparing virtual environment and dependencies..."
	@$(CMD_ENV)

env-win:
	@echo "[*] [Windows] Preparing Windows virtual environment (.venv) and installing dependencies..."
	@powershell -NoProfile -ExecutionPolicy Bypass -File ./build.ps1 -Task env

env-linux:
	@echo "[*] [Linux] Preparing Linux virtual environment (.venv) and installing dependencies..."
	@bash -c "test -d .venv || python3 -m venv .venv; .venv/bin/pip install --upgrade pip; .venv/bin/pip install -r requirements.txt"

env-mac:
	@echo "[*] [macOS] Preparing macOS virtual environment (.venv) and installing dependencies..."
	@bash -c "test -d .venv || python3 -m venv .venv; .venv/bin/pip install --upgrade pip; .venv/bin/pip install -r requirements.txt"

build:
	@echo "[*] [$(PLATFORM)] Compiling standalone distribution binaries..."
	@$(CMD_BUILD)

run:
	@echo "[*] [$(PLATFORM)] Launching NewsAlerts (portable)..."
	@$(CMD_RUN)

run-app:
	@echo "[*] [$(PLATFORM)] Launching NewsAlerts (unpacked app directory)..."
	@$(CMD_RUN_APP)

install-local:
	@echo "[*] [$(PLATFORM)] Installing NewsAlerts to local user app directory..."
	@$(CMD_INSTALL_LOCAL)

installer:
	@echo "[*] [$(PLATFORM)] Compiling Inno Setup Windows installer..."
	@$(CMD_INSTALLER)

test:
	@echo "[*] [$(PLATFORM)] Running unit test suite..."
	@$(CMD_TEST)

verify:
	@echo "[*] [$(PLATFORM)] Executing Deterministic Package Verification Gate..."
	@$(CMD_VERIFY)

check:
	@echo "[*] [$(PLATFORM)] Auditing for leaked secrets..."
	@$(CMD_CHECK)

clean:
	@echo "[*] [$(PLATFORM)] Cleaning build artifacts..."
	@$(CMD_CLEAN)

worktree-list:
	@echo "[*] [$(PLATFORM)] Listing active git worktrees..."
	@$(CMD_WT_LIST)

worktree-new:
	@echo "[*] [$(PLATFORM)] Creating worktree..."
	@$(CMD_WT_NEW)

issue-list:
	@echo "[*] [$(PLATFORM)] Listing open GitHub issues..."
	@$(CMD_ISSUE_LIST)

issue-view:
	@echo "[*] [$(PLATFORM)] Inspecting GitHub issue $(ISSUE)..."
	@$(CMD_ISSUE_VIEW)

wiki-sync:
	@echo "[*] [$(PLATFORM)] Synchronizing GitHub Wiki documentation..."
	@$(CMD_WIKI_SYNC)

help:
	@echo "NewsAlerts Universal Makefile [Platform: $(PLATFORM)]"
	@echo "======================================================="
	@echo "Environment & Setup Targets:"
	@echo "  make env            Auto-detect OS, prepare virtualenv (.venv) & install dependencies"
	@echo "  make env-win        Prepare Windows virtual environment & install dependencies"
	@echo "  make env-linux      Prepare Linux virtual environment & install dependencies"
	@echo "  make env-mac        Prepare macOS virtual environment & install dependencies"
	@echo ""
	@echo "Build & Execution Targets:"
	@echo "  make build          Compile standalone binary / dual distribution package (after make env)"
	@echo "  make run            Launch portable standalone executable"
	@echo "  make run-app        Launch unpacked application from dist/NewsAlerts-App/"
	@echo "  make install-local  Install app to %LOCALAPPDATA%\Programs\NewsAlerts + shortcuts"
	@echo "  make installer      Compile Inno Setup setup executable (requires ISCC)"
	@echo "  make test           Execute unit test suite (tests/test_*.py)"
	@echo "  make verify         Run Deterministic Package Verification Gate"
	@echo "  make check          Audit staged/local files for credentials and secrets"
	@echo "  make clean          Remove build/, dist/, and cached artifacts"
	@echo ""
	@echo "Workflow & Wiki Targets:"
	@echo "  make worktree-list  List active Git worktrees under .worktrees/"
	@echo "  make worktree-new   Create a new isolated worktree (BRANCH=feat/... [BASE=main])"
	@echo "  make issue-list     List open repository issues via GitHub CLI"
	@echo "  make issue-view     Inspect details for an issue (ISSUE=<number>)"
	@echo "  make wiki-sync      Synchronize docs/wiki/ documentation with GitHub Wiki"
	@echo "  make help           Show this usage guide"
