@echo off
cd /d "%~dp0"
echo === NICTO App Launcher ===
echo.

echo [1/3] Starting API server (port 5000)...
set NIKTO_NO_AUTH=1
start /B "NiktoAPI" python packages/nikto-core/src/nikto/__main__.py 5000
timeout /t 30 /nobreak > nul

echo [2/3] Starting Desktop App (port 5173)...
set NODE_OPTIONS=--max-old-space-size=512
cd packages\nikto-desktop
start /B "NiktoDesktop" npx vite --port 5173 --host
cd ..\..
timeout /t 10 /nobreak > nul

echo [3/3] Verifying...
curl -s http://127.0.0.1:5000/health > nul 2>&1
if %errorlevel% equ 0 (
    echo   API: OK
) else (
    echo   API: FAILED - check if python is running
)

curl -s http://127.0.0.1:5173 > nul 2>&1
if %errorlevel% equ 0 (
    echo   Desktop: OK
) else (
    echo   Desktop: FAILED
)

echo.
echo === NICTO is RUNNING ===
echo API:      http://127.0.0.1:5000
echo Desktop:  http://127.0.0.1:5173
echo.
echo Press any key to stop servers...
pause > nul

echo Stopping...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul
echo Done.
