"""
Diagnostic launcher for Memory Vault GUI
This will capture any errors that occur during startup
"""
import sys
import traceback
from pathlib import Path
from datetime import datetime

# Set up error logging
log_file = Path(__file__).parent / "gui_error_log.txt"

try:
    # Change to the correct directory
    import os
    os.chdir(Path(__file__).parent)
    
    # Import and run the GUI
    from src.rag_gui import RAGApp
    
    app = RAGApp()
    app.mainloop()
    
except Exception as e:
    # Log any errors
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"Error at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*80}\n")
        f.write(f"Error: {str(e)}\n\n")
        f.write(traceback.format_exc())
        f.write(f"\n{'='*80}\n")
    
    # Also show a message box
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Memory Vault Error",
        f"Failed to start Memory Vault.\n\n"
        f"Error: {str(e)}\n\n"
        f"Check {log_file} for details."
    )
    root.destroy()
    sys.exit(1)
