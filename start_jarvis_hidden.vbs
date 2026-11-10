' Starts Jarvis with NO black window. Put a shortcut to this file in shell:startup
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
shell.Run Chr(34) & folder & "\start_jarvis.bat" & Chr(34), 0, False
