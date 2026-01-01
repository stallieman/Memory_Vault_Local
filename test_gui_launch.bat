@echo off
REM Test script to diagnose GUI launch issues
echo Testing GUI Launch...
echo Current Directory: %CD%
echo.

cd /d C:\Projecten\memory-vault-main\memory-vault-main
echo Changed to: %CD%
echo.

echo Checking if pythonw.exe exists...
if exist "venv\Scripts\pythonw.exe" (
    echo ✓ pythonw.exe found
) else (
    echo ✗ pythonw.exe NOT found
    pause
    exit /b 1
)

echo.
echo Checking if src\rag_gui.py exists...
if exist "src\rag_gui.py" (
    echo ✓ rag_gui.py found
) else (
    echo ✗ rag_gui.py NOT found
    pause
    exit /b 1
)

echo.
echo Launching GUI with error capture...
venv\Scripts\pythonw.exe src\rag_gui.py

REM If there's an error, it will be written to a log file
if errorlevel 1 (
    echo Error occurred. Check error_log.txt
    pause
)
