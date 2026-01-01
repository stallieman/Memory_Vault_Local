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
    [ValidateSet("watcher", "gui", "cli", "server", "stats", "reindex", "sanity", "new-howto", "help")]
    [string]$Command = "help",
    
    [Parameter(Position=1)]
    [string]$SourceGroup = "",
    
    [Parameter(Position=2)]
    [string]$Title = ""
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
    Write-Host "Usage: .\tasks.ps1 <command> [args]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  watcher              - Start file watcher (monitors C:\Notes)"
    Write-Host "  gui                  - Start GUI application"
    Write-Host "  cli                  - Start CLI (interactive RAG)"
    Write-Host "  server               - Start MCP server"
    Write-Host "  stats                - Show database statistics"
    Write-Host "  reindex              - Full re-ingest (with confirmation)"
    Write-Host "  sanity               - Run sanity check (3 test queries)"
    Write-Host "  new-howto <group> <title> - Create new howto from template"
    Write-Host "  help                 - Show this help"
    Write-Host ""
    Write-Host "Example:"
    Write-Host "  .\tasks.ps1 new-howto elastic 'Kibana data view refresh fields'"
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
    & $VenvPython -c "import sys; sys.path.insert(0, 'src'); from ingestion import DocumentIngestion; ing = DocumentIngestion(); print('Clearing existing data...'); ing.client.delete_collection('knowledge_base'); ing.collection = ing.client.get_or_create_collection(name='knowledge_base', metadata={'description': 'Local knowledge base documents'}, embedding_function=ing.embedding_function); print('Re-ingesting all files...'); ing.ingest_directory(); stats = ing.get_stats(); print('Complete! Total chunks:', stats['total_chunks'])"
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

function New-Howto {
    param(
        [string]$SourceGroup,
        [string]$Title
    )
    
    # Validate arguments
    if (-not $SourceGroup -or -not $Title) {
        Write-Host "ERROR: Missing arguments" -ForegroundColor Red
        Write-Host "Usage: .\tasks.ps1 new-howto <source_group> <title>" -ForegroundColor Yellow
        Write-Host "Example: .\tasks.ps1 new-howto elastic 'Kibana data view refresh fields'"
        exit 1
    }
    
    # Valid source groups
    $validGroups = @("sql", "tdv", "elastic", "python", "docker", "git", "ai", "ebooks", "microsoft", "tools", "personal", "misc")
    if ($SourceGroup -notin $validGroups) {
        Write-Host "ERROR: Invalid source_group '$SourceGroup'" -ForegroundColor Red
        Write-Host "Valid groups: $($validGroups -join ', ')"
        exit 1
    }
    
    # Convert title to kebab-case
    $kebabTitle = $Title.ToLower() -replace '\s+', '-' -replace '[^a-z0-9-]', ''
    
    # Paths
    $notesDir = "C:\Notes"
    $templatePath = Join-Path $notesDir "_howto_template.md"
    $groupDir = Join-Path $notesDir $SourceGroup
    $howtoDir = Join-Path $groupDir "howto"
    $targetPath = Join-Path $howtoDir "$kebabTitle.md"
    
    # Check if template exists
    if (-not (Test-Path $templatePath)) {
        Write-Host "ERROR: Template not found at $templatePath" -ForegroundColor Red
        exit 1
    }
    
    # Ensure directories exist
    if (-not (Test-Path $groupDir)) {
        Write-Host "WARNING: Source group directory '$groupDir' does not exist." -ForegroundColor Yellow
        $confirm = Read-Host "Create it? (y/n)"
        if ($confirm -ne "y") {
            Write-Host "Cancelled." -ForegroundColor Yellow
            return
        }
        New-Item -ItemType Directory -Path $groupDir -Force | Out-Null
        Write-Host "Created: $groupDir" -ForegroundColor Green
    }
    
    if (-not (Test-Path $howtoDir)) {
        New-Item -ItemType Directory -Path $howtoDir -Force | Out-Null
        Write-Host "Created: $howtoDir" -ForegroundColor Green
    }
    
    # Check if file already exists
    if (Test-Path $targetPath) {
        Write-Host "ERROR: File already exists at $targetPath" -ForegroundColor Red
        exit 1
    }
    
    # Read template
    $template = Get-Content $templatePath -Raw -Encoding UTF8
    
    # Get ISO timestamp
    $timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
    
    # Replace placeholders
    $content = $template -replace '<TITEL VAN DEZE HOWTO>', $Title
    $content = $content -replace '<TITEL>', $Title
    $content = $content -replace '<ISO TIMESTAMP zoals 2025-12-31T14:30:00Z>', $timestamp
    $content = $content -replace '<ISO TIMESTAMP>', $timestamp
    $content = $content -replace '<ISO TIMESTAMP indien gewijzigd>', $timestamp
    $content = $content -replace '<sql\|tdv\|elastic\|python\|docker\|git\|ai\|microsoft\|tools\|personal\|misc>', $SourceGroup
    
    # Write file
    $content | Out-File -FilePath $targetPath -Encoding UTF8 -NoNewline
    
    # Get line count
    $lineCount = (Get-Content $targetPath -Encoding UTF8).Count
    
    # Success message
    Write-Host ""
    Write-Host "✅ Created new howto:" -ForegroundColor Green
    Write-Host "   Path: $targetPath" -ForegroundColor Cyan
    Write-Host "   Lines: $lineCount" -ForegroundColor Cyan
    Write-Host "   Source group: $SourceGroup" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Edit the file and replace all <TOKENS> with actual values"
    Write-Host "  2. Remove sections that don't apply"
    Write-Host "  3. Save - the watcher will auto-index it (if running)"
    Write-Host ""
}

# Main switch
switch ($Command) {
    "watcher"   { Start-Watcher }
    "gui"       { Start-Gui }
    "cli"       { Start-Cli }
    "server"    { Start-Server }
    "stats"     { Show-Stats }
    "reindex"   { Start-Reindex }
    "sanity"    { Start-Sanity }
    "new-howto" { New-Howto -SourceGroup $SourceGroup -Title $Title }
    "help"      { Show-Help }
    default     { Show-Help }
}
