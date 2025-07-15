@echo off
title AI Sexter Bot - Auto Startup
color 0A

echo ==========================================
echo    AI SEXTER BOT - AUTO STARTUP
echo ==========================================
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Please run as administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b
)

:: Set paths
set "BOT_DIR=%~dp0"
set "VENV_DIR=%BOT_DIR%venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "PIP_EXE=%VENV_DIR%\Scripts\pip.exe"

echo [INFO] Bot directory: %BOT_DIR%
echo [INFO] Virtual environment: %VENV_DIR%
echo.

:: Create virtual environment if it doesn't exist
if not exist "%VENV_DIR%" (
    echo [INFO] Creating Python virtual environment...
    python -m venv "%VENV_DIR%"
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to create virtual environment!
        echo Please make sure Python 3.8+ is installed
        pause
        exit /b
    )
    echo [SUCCESS] Virtual environment created
)

:: Activate virtual environment
echo [INFO] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

:: Install requirements
echo [INFO] Installing Python requirements...
"%PIP_EXE%" install -r "%BOT_DIR%requirements.txt"
if %errorLevel% neq 0 (
    echo [ERROR] Failed to install requirements!
    pause
    exit /b
)

:: Install additional packages for ZennoPoster
echo [INFO] Installing additional packages...
"%PIP_EXE%" install fastapi uvicorn motor pymongo sentence-transformers chromadb scikit-learn

:: Check if MongoDB is running
echo [INFO] Checking MongoDB service...
sc query MongoDB >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] MongoDB service not found!
    echo [INFO] Starting MongoDB manually...
    start /b mongod --dbpath "%BOT_DIR%data\db" --port 27017
    timeout /t 5 /nobreak >nul
) else (
    echo [SUCCESS] MongoDB service found
)

:: Start the main bot server
echo [INFO] Starting main AI Sexter Bot server...
start "AI Sexter Bot - Main Server" /min "%PYTHON_EXE%" "%BOT_DIR%backend\server.py"
timeout /t 3 /nobreak >nul

:: Start ZennoPoster server
echo [INFO] Starting ZennoPoster API server...
start "AI Sexter Bot - ZennoPoster" /min "%PYTHON_EXE%" "%BOT_DIR%backend\zenno_server.py"
timeout /t 3 /nobreak >nul

:: Start frontend (optional)
echo [INFO] Do you want to start the web interface? (y/n)
set /p START_WEB=
if /i "%START_WEB%"=="y" (
    echo [INFO] Starting web interface...
    cd /d "%BOT_DIR%frontend"
    start "AI Sexter Bot - Web Interface" /min npm start
    cd /d "%BOT_DIR%"
)

echo.
echo ==========================================
echo       AI SEXTER BOT IS RUNNING!
echo ==========================================
echo.
echo Main Server: http://localhost:8001
echo ZennoPoster API: http://192.168.0.16:8080
echo Web Interface: http://localhost:3000
echo.
echo Logs are saved to:
echo - Main: %BOT_DIR%logs\main.log
echo - ZennoPoster: %BOT_DIR%logs\zenno.log
echo.
echo Press any key to view status...
pause >nul

:: Show server status
echo [INFO] Checking server status...
curl -s http://localhost:8001/api/ >nul 2>&1
if %errorLevel% equ 0 (
    echo [SUCCESS] Main server is running
) else (
    echo [ERROR] Main server is not responding
)

curl -s http://localhost:8080/health >nul 2>&1
if %errorLevel% equ 0 (
    echo [SUCCESS] ZennoPoster API is running
) else (
    echo [ERROR] ZennoPoster API is not responding
)

echo.
echo Bot is ready for ZennoPoster connections!
echo Use POST requests to: http://192.168.0.16:8080/message
echo.
echo Press any key to exit (servers will continue running)...
pause >nul