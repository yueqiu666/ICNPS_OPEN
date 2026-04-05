Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "C:\path\to\your\ICNPS_open\icnps.bat" & chr(34), 0
Set WshShell = Nothing