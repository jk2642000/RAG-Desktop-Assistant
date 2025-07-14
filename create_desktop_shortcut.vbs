Set WshShell = CreateObject("WScript.Shell")
Set oMyShortcut = WshShell.CreateShortcut(WshShell.SpecialFolders("Desktop") & "\RAG Desktop Assistant.lnk")
oMyShortcut.TargetPath = WshShell.CurrentDirectory & "\RAG_Desktop_Assistant.bat"
oMyShortcut.WorkingDirectory = WshShell.CurrentDirectory
oMyShortcut.IconLocation = WshShell.CurrentDirectory & "\assets\app_icon.ico"
oMyShortcut.Description = "RAG Desktop Assistant - AI-Powered Document Q&A"
oMyShortcut.Save

WScript.Echo "Desktop shortcut created successfully!"