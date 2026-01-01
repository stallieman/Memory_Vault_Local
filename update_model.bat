@echo off
REM Recreate the grounded RAG model with updated system prompt
echo ============================================================
echo Recreating rag-grounded-nemo model with quote requirements
echo ============================================================
echo.

echo Checking if base model exists...
ollama list | findstr "mistral-nemo:12b-instruct-2407-q4_K_M" >nul 2>&1
if errorlevel 1 (
    echo Base model not found. Pulling...
    ollama pull mistral-nemo:12b-instruct-2407-q4_K_M
)

echo.
echo Creating grounded model from Modelfile...
ollama create rag-grounded-nemo -f ollama\Modelfile.rag-grounded

echo.
echo ============================================================
echo Model updated! The RAG system will now enforce quotes.
echo ============================================================
echo.
echo You can test it by launching the GUI and asking a question.
pause
