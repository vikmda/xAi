@echo off
title AI Sexter Bot - Shutdown
color 0C

echo ==========================================
echo    AI SEXTER BOT - SHUTDOWN
echo ==========================================
echo.

:: Kill Python processes running the bot
echo [INFO] Stopping AI Sexter Bot servers...

taskkill /f /im python.exe /fi "WINDOWTITLE eq AI Sexter Bot - Main Server" >nul 2>&1
taskkill /f /im python.exe /fi "WINDOWTITLE eq AI Sexter Bot - ZennoPoster" >nul 2>&1

:: Kill any remaining Python processes (be careful!)
echo [INFO] Stopping any remaining Python processes...
tasklist /fi "imagename eq python.exe" /fo table | findstr python.exe >nul 2>&1
if %errorLevel% equ 0 (
    echo [WARNING] Found running Python processes
    echo [INFO] Do you want to kill ALL Python processes? (y/n)
    set /p KILL_ALL=
    if /i "%KILL_ALL%"=="y" (
        taskkill /f /im python.exe >nul 2>&1
        echo [SUCCESS] All Python processes stopped
    )
)

:: Stop Node.js (frontend)
echo [INFO] Stopping web interface...
taskkill /f /im node.exe >nul 2>&1

:: Stop MongoDB (if started manually)
echo [INFO] Stopping MongoDB (if running)...
taskkill /f /im mongod.exe >nul 2>&1

echo.
echo [SUCCESS] AI Sexter Bot has been stopped
echo.
echo Press any key to exit...
pause >nul