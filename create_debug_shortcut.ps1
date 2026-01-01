# Diagnostic Shortcut Creator for Memory Vault
# Creates a shortcut that will help diagnose startup issues

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "Memory Vault (Debug).lnk"

Write-Host "Creating diagnostic shortcut..." -ForegroundColor Yellow

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)

$shortcut.TargetPath = "C:\Projecten\memory-vault-main\memory-vault-main\venv\Scripts\pythonw.exe"
$shortcut.Arguments = "launch_gui_debug.py"
$shortcut.WorkingDirectory = "C:\Projecten\memory-vault-main\memory-vault-main"
$shortcut.Description = "Memory Vault - Debug Mode (captures errors to log file)"
$shortcut.IconLocation = "C:\Projecten\memory-vault-main\memory-vault-main\venv\Scripts\pythonw.exe,0"

$shortcut.Save()

Write-Host "Debug shortcut created at: $shortcutPath" -ForegroundColor Green
Write-Host "`nThis shortcut will:" -ForegroundColor Cyan
Write-Host "  - Launch Memory Vault"
Write-Host "  - Capture any errors to gui_error_log.txt"
Write-Host "  - Show an error dialog if something goes wrong"
Write-Host "`nTry launching from this shortcut to see if there are any errors." -ForegroundColor Yellow

[System.Runtime.Interopservices.Marshal]::ReleaseComObject($shell) | Out-Null
