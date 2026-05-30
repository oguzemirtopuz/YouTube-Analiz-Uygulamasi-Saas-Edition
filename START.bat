@echo off
cd /d "%~dp0"
echo Starting the application...
start /min pythonw server.pyw
exit