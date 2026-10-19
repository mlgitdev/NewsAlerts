@echo off
rem NewsAlerts Windows Make Wrapper
rem Automatically forwards 'make <target>' to PowerShell build automation or test suites.

if "%1"=="" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1" -Task help
    exit /b 0
)

if /I "%1"=="help" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1" -Task help
    exit /b 0
)

if /I "%1"=="test" (
    if exist "%~dp0.venv\Scripts\python.exe" (
        "%~dp0.venv\Scripts\python.exe" -m unittest discover -s "%~dp0tests" -p "test_*.py"
    ) else if exist "%~dp0..\..\.venv\Scripts\python.exe" (
        "%~dp0..\..\.venv\Scripts\python.exe" -m unittest discover -s "%~dp0tests" -p "test_*.py"
    ) else (
        python -m unittest discover -s "%~dp0tests" -p "test_*.py"
    )
    exit /b %errorlevel%
)

if /I "%1"=="verify" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1" -Task verify-packages
    exit /b %errorlevel%
)

if /I "%1"=="worktree-list" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1" -Task worktree-list
    exit /b %errorlevel%
)

if /I "%1"=="worktree-new" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1" -Task worktree-new -Branch "%2" -Base "%3"
    exit /b %errorlevel%
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1" -Task %1
exit /b %errorlevel%
