@echo off
title AI Sexter Bot - Installation
color 0B

echo ==========================================
echo    AI SEXTER BOT - INSTALLATION
echo ==========================================
echo.
echo This script will install AI Sexter Bot on Windows 11 Pro
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Please run as administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b
)

:: Set installation directory
set "INSTALL_DIR=%~dp0"
echo [INFO] Installation directory: %INSTALL_DIR%

:: Step 1: Check Python
echo [STEP 1] Checking Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH"
    pause
    exit /b
)

python -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
echo [SUCCESS] Python is installed

:: Step 2: Check Node.js
echo.
echo [STEP 2] Checking Node.js installation...
node --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Node.js is not installed!
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b
)

node --version
echo [SUCCESS] Node.js is installed

:: Step 3: Check MongoDB
echo.
echo [STEP 3] Checking MongoDB installation...
mongod --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] MongoDB is not installed!
    echo Downloading MongoDB Community Edition...
    
    :: Create temp directory
    mkdir "%TEMP%\mongodb_install" >nul 2>&1
    
    :: Download MongoDB (this is a placeholder - in real scenario, provide actual download)
    echo [INFO] Please download MongoDB Community Edition from:
    echo https://www.mongodb.com/try/download/community
    echo.
    echo Install it with default settings
    echo.
    set /p MONGODB_INSTALLED=Press Y when MongoDB is installed: 
    
    :: Check again
    mongod --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo [ERROR] MongoDB installation failed!
        pause
        exit /b
    )
)

mongod --version | findstr "version"
echo [SUCCESS] MongoDB is installed

:: Step 4: Create directories
echo.
echo [STEP 4] Creating directories...
mkdir "%INSTALL_DIR%data" >nul 2>&1
mkdir "%INSTALL_DIR%data\db" >nul 2>&1
mkdir "%INSTALL_DIR%logs" >nul 2>&1
mkdir "%INSTALL_DIR%backend" >nul 2>&1
mkdir "%INSTALL_DIR%frontend" >nul 2>&1
echo [SUCCESS] Directories created

:: Step 5: Create Python virtual environment
echo.
echo [STEP 5] Creating Python virtual environment...
python -m venv "%INSTALL_DIR%venv"
if %errorLevel% neq 0 (
    echo [ERROR] Failed to create virtual environment!
    pause
    exit /b
)
echo [SUCCESS] Virtual environment created

:: Step 6: Install Python packages
echo.
echo [STEP 6] Installing Python packages...
call "%INSTALL_DIR%venv\Scripts\activate.bat"
pip install --upgrade pip
pip install fastapi uvicorn motor pymongo sentence-transformers chromadb scikit-learn python-dotenv pydantic
if %errorLevel% neq 0 (
    echo [ERROR] Failed to install Python packages!
    pause
    exit /b
)
echo [SUCCESS] Python packages installed

:: Step 7: Install Node.js packages
echo.
echo [STEP 7] Installing Node.js packages...
cd /d "%INSTALL_DIR%frontend"
if exist package.json (
    npm install
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to install Node.js packages!
        pause
        exit /b
    )
    echo [SUCCESS] Node.js packages installed
) else (
    echo [INFO] No package.json found, skipping Node.js installation
)

:: Step 8: Configure Windows Firewall
echo.
echo [STEP 8] Configuring Windows Firewall...
netsh advfirewall firewall add rule name="AI Sexter Bot - Main" dir=in action=allow protocol=TCP localport=8001 >nul 2>&1
netsh advfirewall firewall add rule name="AI Sexter Bot - ZennoPoster" dir=in action=allow protocol=TCP localport=8080 >nul 2>&1
netsh advfirewall firewall add rule name="AI Sexter Bot - Web" dir=in action=allow protocol=TCP localport=3000 >nul 2>&1
netsh advfirewall firewall add rule name="MongoDB" dir=in action=allow protocol=TCP localport=27017 >nul 2>&1
echo [SUCCESS] Firewall rules added

:: Step 9: Create environment file
echo.
echo [STEP 9] Creating environment configuration...
cd /d "%INSTALL_DIR%backend"
echo MONGO_URL=mongodb://localhost:27017 > .env
echo DB_NAME=sexter_bot >> .env
echo HOST=0.0.0.0 >> .env
echo PORT=8001 >> .env
echo ZENNO_HOST=192.168.0.16 >> .env
echo ZENNO_PORT=8080 >> .env
echo [SUCCESS] Environment configuration created

:: Step 10: Test installation
echo.
echo [STEP 10] Testing installation...
echo [INFO] Starting MongoDB...
start /b mongod --dbpath "%INSTALL_DIR%data\db" --port 27017
timeout /t 5 /nobreak >nul

echo [INFO] Testing Python imports...
python -c "import fastapi, uvicorn, motor, pymongo, sentence_transformers, chromadb; print('All imports successful')"
if %errorLevel% neq 0 (
    echo [ERROR] Python import test failed!
    pause
    exit /b
)

echo [SUCCESS] Installation test passed

:: Step 11: Create desktop shortcuts
echo.
echo [STEP 11] Creating desktop shortcuts...
set "DESKTOP=%USERPROFILE%\Desktop"

:: Create start shortcut
echo Set WshShell = WScript.CreateObject("WScript.Shell") > "%TEMP%\create_shortcut.vbs"
echo Set Shortcut = WshShell.CreateShortcut("%DESKTOP%\Start AI Sexter Bot.lnk") >> "%TEMP%\create_shortcut.vbs"
echo Shortcut.TargetPath = "%INSTALL_DIR%start_sexter_bot.bat" >> "%TEMP%\create_shortcut.vbs"
echo Shortcut.WorkingDirectory = "%INSTALL_DIR%" >> "%TEMP%\create_shortcut.vbs"
echo Shortcut.Description = "Start AI Sexter Bot" >> "%TEMP%\create_shortcut.vbs"
echo Shortcut.Save >> "%TEMP%\create_shortcut.vbs"
cscript //nologo "%TEMP%\create_shortcut.vbs"

:: Create stop shortcut
echo Set WshShell = WScript.CreateObject("WScript.Shell") > "%TEMP%\create_shortcut2.vbs"
echo Set Shortcut = WshShell.CreateShortcut("%DESKTOP%\Stop AI Sexter Bot.lnk") >> "%TEMP%\create_shortcut2.vbs"
echo Shortcut.TargetPath = "%INSTALL_DIR%stop_sexter_bot.bat" >> "%TEMP%\create_shortcut2.vbs"
echo Shortcut.WorkingDirectory = "%INSTALL_DIR%" >> "%TEMP%\create_shortcut2.vbs"
echo Shortcut.Description = "Stop AI Sexter Bot" >> "%TEMP%\create_shortcut2.vbs"
echo Shortcut.Save >> "%TEMP%\create_shortcut2.vbs"
cscript //nologo "%TEMP%\create_shortcut2.vbs"

del "%TEMP%\create_shortcut.vbs" >nul 2>&1
del "%TEMP%\create_shortcut2.vbs" >nul 2>&1

echo [SUCCESS] Desktop shortcuts created

:: Installation complete
echo.
echo ==========================================
echo     INSTALLATION COMPLETED!
echo ==========================================
echo.
echo AI Sexter Bot has been successfully installed!
echo.
echo Installation directory: %INSTALL_DIR%
echo.
echo Next steps:
echo 1. Copy your bot files to the installation directory
echo 2. Run "Start AI Sexter Bot" from desktop
echo 3. Access web interface at http://localhost:3000
echo 4. Use ZennoPoster API at http://192.168.0.16:8080
echo.
echo Network configuration:
echo - Main API: http://192.168.0.16:8001
echo - ZennoPoster: http://192.168.0.16:8080
echo - Web Interface: http://192.168.0.16:3000
echo.
echo Press any key to exit...
pause >nul