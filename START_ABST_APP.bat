@echo off
title ABST Application Launcher - EXACT DATA
color 0A

echo.
echo ========================================
echo    ABST Application Launcher
echo ========================================
echo.
echo This will automatically set up and run your ABST application!
echo.
echo INCLUDES YOUR EXACT DATA:
echo - All your real facilities
echo - All your real residents  
echo - All your real ADLs
echo - All your real scheduling data
echo - All your real staff assignments
echo - All your real shift templates
echo.
echo What happens automatically:
echo - Builds Docker image with your exact data
echo - Starts the application
echo - Opens your browser automatically
echo.
echo Press any key to continue...
pause >nul

echo.
echo Building Docker image (this may take 5-10 minutes first time)...
echo Checking for Dockerfile...

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
echo Script directory: %SCRIPT_DIR%

REM Check if Dockerfile exists in the script directory
if not exist "%SCRIPT_DIR%Dockerfile_exact_data" (
    echo ❌ Dockerfile_exact_data not found in: %SCRIPT_DIR%
    echo Please make sure you extracted the zip file completely.
    echo You should see Dockerfile_exact_data in the same folder as this .bat file.
    echo.
    echo Files in current directory:
    dir
    pause
    exit /b 1
)

echo ✅ Dockerfile found, building image...
cd /d "%SCRIPT_DIR%"
docker build -f Dockerfile_exact_data -t abst-exact-data .

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Error building Docker image!
    echo Please make sure Docker Desktop is running and try again.
    pause
    exit /b 1
)

echo.
echo ✅ Docker image built successfully!
echo Starting application...
docker run -p 8000:8000 abst-exact-data

echo.
echo Application stopped.
pause
