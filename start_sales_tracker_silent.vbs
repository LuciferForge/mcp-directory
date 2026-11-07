Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\ManjunathG\.gemini\antigravity\scratch\protodex-revamp"
WshShell.Run "pythonw track_sales.py --loop", 0, False
