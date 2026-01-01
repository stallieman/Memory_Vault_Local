# Create Desktop Shortcut for Memory Vault
# Run this script once to create the shortcut

$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Memory Vault.lnk"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "pythonw.exe"
$Shortcut.Arguments = "src\rag_gui.py"
$Shortcut.WorkingDirectory = "C:\Projecten\memory-vault-main\memory-vault-main"
$Shortcut.IconLocation = "C:\Windows\System32\shell32.dll,13"
$Shortcut.Description = "Memory Vault - Grounded RAG with Citation Enforcement"
$Shortcut.Save()

Write-Host "✅ Desktop shortcut created: $ShortcutPath" -ForegroundColor Green
Write-Host ""
Write-Host "Note: The shortcut uses pythonw.exe (no console window)."
Write-Host "Make sure your venv's python is in PATH, or edit the shortcut to use:"
Write-Host "  C:\Projecten\memory-vault-main\memory-vault-main\venv\Scripts\pythonw.exe"
