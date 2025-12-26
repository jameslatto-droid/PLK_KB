@echo off
REM Whisper NPU GUI Launcher
REM Launches the Windows GUI for Whisper transcription

python whisper_gui.py
if errorlevel 1 (
    echo.
    echo Error launching GUI. Make sure Python and dependencies are installed.
    echo Run: .\install_deps.ps1
    pause
)
