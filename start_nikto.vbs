' NICTO Launcher - Creates persistent processes
Dim WshShell
Set WshShell = CreateObject("WScript.Shell")

Dim niktoDir
niktoDir = CreateObject("Scripting.FileSystemObject").GetAbsolutePathName(".")

WshShell.Run "cmd /c python nikto_cli/main.py serve --no-auth --port 5000", 0, False
WScript.Sleep 20000

WshShell.Run "cmd /c set NODE_OPTIONS=--max-old-space-size=512 && npx vite --port 5173 --host", 0, False

WScript.Sleep 5000
WshShell.Popup "NICTO is running!" & vbCrLf & "API: http://127.0.0.1:5000" & vbCrLf & "Desktop: http://127.0.0.1:5173", 3, "NICTO", 64
