@echo off
title FinVault Finance Intelligence Platform Manager
setlocal enabledelayedexpansion

:MENU
cls
echo ======================================================================
echo          AUTONOMOUS STUDENT FINANCE INTELLIGENCE PLATFORM (FINVAULT)
echo ======================================================================
echo.
echo   [1] Start Platform in NATIVE Mode (Local Python + .NET)
echo   [2] Start Platform in DOCKER Mode (Full Container Stack + Monitoring)
echo   [3] Stop DOCKER Mode Containers
echo   [4] Stop DOCKER Mode Containers and Clean Volumes
echo   [5] Run Integration Test Suite
echo   [6] Show System Monitoring Access URLs
echo   [7] Exit
echo.
echo ======================================================================
set /p opt="Choose an option [1-7]: "

if "%opt%"=="1" goto NATIVE
if "%opt%"=="2" goto DOCKER_UP
if "%opt%"=="3" goto DOCKER_DOWN
if "%opt%"=="4" goto DOCKER_CLEAN
if "%opt%"=="5" goto RUN_TESTS
if "%opt%"=="6" goto MON_URLS
if "%opt%"=="7" goto EXIT
goto MENU

:NATIVE
cls
echo ======================================================================
echo                  STARTING FINVAULT IN NATIVE MODE
echo ======================================================================
echo.
:: Get the directory of this batch file
set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo [1/3] Launching FastAPI Backend (Uvicorn)...
cd backend
start "FinVault Backend (FastAPI)" cmd /k "set PYTHONIOENCODING=utf-8&& python main.py"
cd ..

echo.
echo Waiting 6 seconds for the Backend RAG engine to initialize Qdrant mock...
timeout /t 6 /nobreak >nul

echo.
echo [2/3] Launching .NET Core Frontend WebApp...
cd frontend
start "FinVault Frontend (.NET)" cmd /k "dotnet run"
cd ..

echo.
echo Waiting 5 seconds for the Frontend web host to initialize...
timeout /t 5 /nobreak >nul

echo.
echo [3/3] Opening FinVault portal in default browser...
start http://localhost:5254

echo.
echo Native mode is now running.
echo - Student/Officer Portal:  http://localhost:5254
echo - FastAPI Backend Gateway: http://localhost:8000
echo.
pause
goto MENU

:DOCKER_UP
cls
echo ======================================================================
echo                  STARTING FINVAULT IN DOCKER MODE
echo ======================================================================
echo.
echo Building and launching container services...
echo (Backend, Frontend, Redis, Qdrant, Kafka, Prometheus, Grafana, Loki)
echo.
docker-compose -f deployment/docker/docker-compose.yml up --build -d
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to start docker-compose. Make sure Docker Desktop is running.
    pause
    goto MENU
)
echo.
echo Waiting 10 seconds for services to bootstrap...
timeout /t 10 /nobreak >nul
echo.
echo Opening Student Portal (http://localhost:5000) and Grafana (http://localhost:3000)...
start http://localhost:5000
start http://localhost:3000
goto MON_URLS

:DOCKER_DOWN
cls
echo ======================================================================
echo                  STOPPING DOCKER CONTAINERS
echo ======================================================================
echo.
docker-compose -f deployment/docker/docker-compose.yml down
echo.
echo Containers stopped successfully.
pause
goto MENU

:DOCKER_CLEAN
cls
echo ======================================================================
echo             STOPPING CONTAINERS AND DELETING VOLUMES
echo ======================================================================
echo.
echo WARNING: This will delete Qdrant databases and Kafka log partitions.
set /p confirm="Are you sure? (Y/N): "
if /i "%confirm%"=="Y" (
    docker-compose -f deployment/docker/docker-compose.yml down -v
    echo.
    echo Volumes cleaned.
) else (
    echo Operation cancelled.
)
pause
goto MENU

:RUN_TESTS
cls
echo ======================================================================
echo                     RUNNING INTEGRATION TESTS
echo ======================================================================
echo.
python testing/test_platform.py
echo.
pause
goto MENU

:MON_URLS
cls
echo ======================================================================
echo                 FINVAULT PLATFORM ACCESS DIRECTORY
echo ======================================================================
echo.
echo   ✦ Student & Officer Web Portal : http://localhost:5000
echo   ✦ FastAPI Backend API Gateway  : http://localhost:8000/docs
echo   ✦ Grafana Monitoring Console   : http://localhost:3000
echo                                     (User: admin / Pass: admin)
echo   ✦ Prometheus Metrics Endpoint  : http://localhost:9090
echo   ✦ Loki Structured Log Stream   : http://localhost:3100
echo.
echo ======================================================================
echo.
pause
goto MENU

:EXIT
echo Exiting FinVault runner. Goodbye!
timeout /t 2 >nul
exit
