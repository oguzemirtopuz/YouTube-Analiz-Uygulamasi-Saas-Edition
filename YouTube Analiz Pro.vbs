Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

basePath = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = basePath

' Run pythonw server.pyw hidden (0)
shell.Run "pythonw server.pyw", 0, False
