' Adaptive Resume AI • Desktop Studio Launcher
Option Explicit
Dim WshShell, fso, scriptDir, repoRoot, pythonwPath, pyScript

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
repoRoot = fso.GetParentFolderName(scriptDir)
pyScript = repoRoot & "\scripts\web_ui.py"

' Set working directory to project root
WshShell.CurrentDirectory = repoRoot

' Attempt pythonw first (no console window)
On Error Resume Next
WshShell.Run "pythonw.exe """ & pyScript & """", 0, False
If Err.Number <> 0 Then
    Err.Clear
    WshShell.Run "python.exe """ & pyScript & """", 0, False
End If
On Error GoTo 0

' Allow server moment to initialize if starting fresh, then open browser
WScript.Sleep 600
WshShell.Run "http://localhost:8765"
