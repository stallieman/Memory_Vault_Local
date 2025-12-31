<#
.SYNOPSIS
    Task runner for Memory Vault Local Knowledge Base
.DESCRIPTION
    Start watcher, GUI, CLI, server, view stats, or reindex.
.EXAMPLE
    .\tasks.ps1 watcher
    .\tasks.ps1 gui
    .\tasks.ps1 stats
#>

param(
    [Parameter(Position=0)]
    [ValidateSet("watcher", "gui", "cli", "server", "stats", "reindex", "sanity", "help")]
    [string]$Command = "help"
)

# Config
$RepoRoot = $PSScriptRoot
$VenvPython = Join-Path $RepoRoot "venv\Scripts\python.exe"
$SrcDir = Join-Path $RepoRoot "src"

# Ensure UTF-8 output
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

function Test-Venv {
    if (-not (Test-Path $VenvPython)) {
        Write-Host "ERROR: Virtual environment not found at $VenvPython" -ForegroundColor Red
        Write-Host "Run: python -m venv venv && .\venv\Scripts\Activate.ps1 && pip install -r requirements.txt"
        exit 1
    }
}

function Show-Help {
    Write-Host ""
    Write-Host "Memory Vault Task Runner" -ForegroundColor Cyan
    Write-Host "========================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\tasks.ps1 <command>" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  watcher  - Start file watcher (monitors C:\Notes)"
    Write-Host "  gui      - Start GUI application"
    Write-Host "  cli      - Start CLI (interactive RAG)"
    Write-Host "  server   - Start MCP server"
    Write-Host "  stats    - Show database statistics"
    Write-Host "  reindex  - Full re-ingest (with confirmation)"
    Write-Host "  sanity   - Run sanity check (3 test queries)"
    Write-Host "  help     - Show this help"
    Write-Host ""
}

function Start-Watcher {
    Test-Venv
    Write-Host ""
    Write-Host "Starting File Watcher..." -ForegroundColor Green
    Write-Host "Monitoring: C:\Notes" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
    Write-Host ""
    & $VenvPython (Join-Path $SrcDir "watcher.py")
}

function Start-Gui {
    Test-Venv
    Write-Host ""
    Write-Host "Starting GUI..." -ForegroundColor Green
    & $VenvPython (Join-Path $SrcDir "rag_gui.py")
}

function Start-Cli {
    Test-Venv
    Write-Host ""
    Write-Host "Starting CLI..." -ForegroundColor Green
    & $VenvPython (Join-Path $SrcDir "local_rag_ollama.py")
}

function Start-Server {
    Test-Venv
    Write-Host ""
    Write-Host "Starting MCP Server..." -ForegroundColor Green
    & $VenvPython (Join-Path $SrcDir "server.py")
}

function Show-Stats {
    Test-Venv
    Write-Host ""
    Write-Host "Database Statistics" -ForegroundColor Cyan
    Write-Host "===================" -ForegroundColor Cyan
    
    Push-Location $RepoRoot
    & $VenvPython -c "import sys; sys.path.insert(0, 'src'); from ingestion import DocumentIngestion; ing = DocumentIngestion(); stats = ing.get_stats(); print('Total chunks:', stats['total_chunks']); print('Collection:', stats['collection_name']); print('Data dir:', stats['data_directory']); print('DB path:', stats['db_path'])"
    Pop-Location
}

function Start-Reindex {
    Test-Venv
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host " FULL RE-INDEX WARNING" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "This will:" -ForegroundColor Yellow
    Write-Host "  - Delete ALL existing chunks from ChromaDB"
    Write-Host "  - Re-ingest ALL files from C:\Notes"
    Write-Host "  - Take several minutes (~35k chunks)"
    Write-Host ""
    
    # Show current stats first
    Show-Stats
    Write-Host ""
    
    $confirm = Read-Host "ARE YOU SURE? Type 'yes' to continue"
    if ($confirm -ne "yes") {
        Write-Host "Cancelled." -ForegroundColor Yellow
        return
    }
    
    Write-Host ""
    Write-Host "Starting full re-ingest..." -ForegroundColor Green
    
    Push-Location $RepoRoot
    & $VenvPython -c "import sys; sys.path.insert(0, 'src'); from ingestion import DocumentIngestion; ing = DocumentIngestion(); print('Clearing existing data...'); ing.collection.delete(where={}); print('Re-ingesting all files...'); ing.ingest_directory(); stats = ing.get_stats(); print('Complete! Total chunks:', stats['total_chunks'])"
    Pop-Location
    
    Write-Host ""
    Write-Host "Re-index complete!" -ForegroundColor Green
}

function Start-Sanity {
    Test-Venv
    Write-Host ""
    Write-Host "Running Sanity Check..." -ForegroundColor Green
    
    Push-Location $RepoRoot
    & $VenvPython (Join-Path $RepoRoot "sanity_check.py")
    Pop-Location
}

# Main switch
switch ($Command) {
    "watcher" { Start-Watcher }
    "gui"     { Start-Gui }
    "cli"     { Start-Cli }
    "server"  { Start-Server }
    "stats"   { Show-Stats }
    "reindex" { Start-Reindex }
    "sanity"  { Start-Sanity }
    "help"    { Show-Help }
    default   { Show-Help }
}
