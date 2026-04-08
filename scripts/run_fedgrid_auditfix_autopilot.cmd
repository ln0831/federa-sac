@echo off
setlocal
"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "C:\Users\ASUS\Desktop\runtime_bundle\scripts\run_fedgrid_auditfix_autopilot.ps1" -RootDir "C:\Users\ASUS\Desktop\runtime_bundle" -PythonExe "D:\Anaconda\envs\tianshou_env\python.exe" -IntervalSec 300
exit /b %ERRORLEVEL%
