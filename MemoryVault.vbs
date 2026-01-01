' Memory Vault - Invisible Launcher
' Double-click this file to launch Memory Vault without any console window

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Projecten\memory-vault-main\memory-vault-main\src"
WshShell.Run """C:\Projecten\memory-vault-main\memory-vault-main\venv\Scripts\pythonw.exe"" rag_gui.py", 0, False
