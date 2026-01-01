# Fix Memory Vault Desktop Shortcut
# This script updates the shortcut to include the correct working directory

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "Memory Vault.lnk"

if (Test-Path $shortcutPath) {
    Write-Host "Found existing shortcut at: $shortcutPath" -ForegroundColor Green
    
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    
    Write-Host "`nCurrent Settings:" -ForegroundColor Yellow
    Write-Host "  Target: $($shortcut.TargetPath)"
    Write-Host "  Arguments: $($shortcut.Arguments)"
    Write-Host "  Start In: $($shortcut.WorkingDirectory)"
    Write-Host "  Icon: $($shortcut.IconLocation)"
    
    # Update the shortcut
    $shortcut.TargetPath = "C:\Projecten\memory-vault-main\memory-vault-main\venv\Scripts\pythonw.exe"
    $shortcut.Arguments = "src\rag_gui.py"
    $shortcut.WorkingDirectory = "C:\Projecten\memory-vault-main\memory-vault-main"
    $shortcut.Description = "Memory Vault - Grounded RAG System"
    $shortcut.IconLocation = "C:\Projecten\memory-vault-main\memory-vault-main\venv\Scripts\pythonw.exe,0"
    
    $shortcut.Save()
    
    Write-Host "`nShortcut updated successfully!" -ForegroundColor Green
    Write-Host "`nNew Settings:" -ForegroundColor Yellow
    Write-Host "  Target: $($shortcut.TargetPath)"
    Write-Host "  Arguments: $($shortcut.Arguments)"
    Write-Host "  Start In: $($shortcut.WorkingDirectory)"
    
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($shell) | Out-Null
} else {
    Write-Host "Shortcut not found at: $shortcutPath" -ForegroundColor Red
    Write-Host "Creating new shortcut..." -ForegroundColor Yellow
    
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    
    $shortcut.TargetPath = "C:\Projecten\memory-vault-main\memory-vault-main\venv\Scripts\pythonw.exe"
    $shortcut.Arguments = "src\rag_gui.py"
    $shortcut.WorkingDirectory = "C:\Projecten\memory-vault-main\memory-vault-main"
    $shortcut.Description = "Memory Vault - Grounded RAG System"
    $shortcut.IconLocation = "C:\Projecten\memory-vault-main\memory-vault-main\venv\Scripts\pythonw.exe,0"
    
    $shortcut.Save()
    
    Write-Host "Shortcut created successfully at: $shortcutPath" -ForegroundColor Green
    
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($shell) | Out-Null
}

Write-Host "`nYou can now try launching Memory Vault from the desktop shortcut." -ForegroundColor Cyan
