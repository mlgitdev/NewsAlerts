# -----------------------------------------------------------------------------
# NewsAlerts Universal Cross-Platform Makefile
# Compatible with Windows (GNU Make / ezwinports / winget), Linux, and macOS
# -----------------------------------------------------------------------------

.PHONY: all build run test verify check clean worktree-list worktree-new help

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

    CMD_BUILD   := $(POWERSHELL) -File ./build.ps1 -Task build
    CMD_RUN     := $(POWERSHELL) -File ./build.ps1 -Task run
    CMD_CLEAN   := $(POWERSHELL) -File ./build.ps1 -Task clean
    CMD_CHECK   := $(POWERSHELL) -File ./build.ps1 -Task check
    CMD_VERIFY  := $(POWERSHELL) -File ./build.ps1 -Task verify-packages
    CMD_TEST    := $(PYTHON) -m unittest discover -s tests -p "test_*.py"
    CMD_WT_LIST := $(POWERSHELL) -File ./build.ps1 -Task worktree-list
    CMD_WT_NEW  := $(POWERSHELL) -File ./build.ps1 -Task worktree-new -Branch "$(BRANCH)" -Base "$(BASE)"
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

    CMD_BUILD   := $(PYTHON) -m pip install -r requirements.txt
    CMD_RUN     := ./run.sh
    CMD_CLEAN   := rm -rf build/ dist/ .venv/ .pytest_cache/ __pycache__/ app/__pycache__/ tests/__pycache__/ *.spec.bak
    CMD_CHECK   := git diff --staged --name-only | grep -E "keys|secret|token|\.env" && exit 1 || echo "[OK] No secrets found in staged files."
    CMD_VERIFY  := $(PYTHON) scripts/verify-packages.py
    CMD_TEST    := $(PYTHON) -m unittest discover -s tests -p "test_*.py"
    CMD_WT_LIST := ./scripts/worktree.sh list
    CMD_WT_NEW  := ./scripts/worktree.sh new "$(BRANCH)" "$(BASE)"
endif

BRANCH ?=
BASE ?= main

all: help

build:
	@echo "[*] [$(PLATFORM)] Executing build task..."
	@$(CMD_BUILD)

run:
	@echo "[*] [$(PLATFORM)] Launching NewsAlerts..."
	@$(CMD_RUN)

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

help:
	@echo "NewsAlerts Universal Makefile [Platform: $(PLATFORM)]"
	@echo "======================================================="
	@echo "Targets:"
	@echo "  make build          Build portable executable [Windows] or install dependencies [Unix]"
	@echo "  make run            Launch the application"
	@echo "  make test           Execute unit test suite (tests/test_*.py)"
	@echo "  make verify         Run Deterministic Package Verification Gate"
	@echo "  make check          Audit staged/local files for credentials and secrets"
	@echo "  make clean          Remove build/, dist/, and cached artifacts"
	@echo "  make worktree-list  List active Git worktrees under .worktrees/"
	@echo "  make worktree-new   Create a new isolated worktree (BRANCH=feat/... [BASE=main])"
	@echo "  make help           Show this usage guide"
