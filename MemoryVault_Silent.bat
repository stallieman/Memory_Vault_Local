@echo off
REM Memory Vault - Silent Launcher (no console window)
REM This uses pythonw.exe from the virtual environment

cd /d "C:\Projecten\memory-vault-main\memory-vault-main\src"
start "" "C:\Projecten\memory-vault-main\memory-vault-main\venv\Scripts\pythonw.exe" rag_gui.py
