Version 0.012
Now with drag and drop

How to use

If you have python installed you can just click the file NestZ.pyw
If not...
Save the previous Python program as NestZ.pyw.
Save the code above as NestZ.bat in the same folder.
Double-click NestZ.bat
New version with Progress Bar

What the script does
Checks that NestZ.pyw is next to the .bat
Looks for python or py in PATH
If missing → tries winget first, then falls back to downloading the official Python 3.12 installer and installs it silently (PrependPath=1)
Creates a Desktop shortcut named “Nested ZIP Extractor” that launches the script

Notes

The script works on Windows 10 / 11.
Admin rights are not required for a per-user install.
After a fresh Python install you may need to open a new Command Prompt if the PATH has not refreshed yet (the script tries to refresh it automatically).
The shortcut uses a generic icon (shell32.dll,45). You can change the icon later by right-clicking the shortcut → Properties → Change Icon.

If you use linux, just open terminal, install python, and run this command:
cd "Folder where file is"
python NestZ.pyw
