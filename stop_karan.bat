@echo off
echo Stopping all Karan AI processes...

REM Kill any process using port 2000
for /f "tokens=5" %%a in ('netstat -aon ^| find ":2000" ^| find "LISTENING"') do (
    echo Stopping process on port 2000 (PID: %%a)
    taskkill /F /PID %%a 2>nul
)

REM Kill all Python processes
echo Stopping all Python processes...
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM python3.exe /T 2>nul
taskkill /F /IM pythonw.exe /T 2>nul

REM Kill Flask development server if running
echo Stopping Flask servers...
taskkill /F /FI "WINDOWTITLE eq Flask" 2>nul

echo.
echo All Karan AI processes have been stopped.
echo If you see any error messages above, it just means some processes weren't running.
echo.
pause
