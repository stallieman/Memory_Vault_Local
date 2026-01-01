@echo off
title Memory Vault - Grounded RAG
cd /d "%~dp0"
call venv\Scripts\activate.bat
cd src
python rag_gui.py
pause
