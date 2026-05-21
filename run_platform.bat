@echo off
title FinVault Finance Intelligence Platform Runner
setlocal enabledelayedexpansion

cls
echo ======================================================================
echo          AUTONOMOUS STUDENT FINANCE INTELLIGENCE PLATFORM (FINVAULT)
echo ======================================================================
echo.
echo [1/3] Launching FinVault Container Stack via Docker Compose...
echo (Backend, Frontend, Redis, Qdrant, Kafka, Prometheus, Grafana, Loki)
echo.

docker-compose -f deployment/docker/docker-compose.yml up --build -d
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to start docker-compose. Make sure Docker Desktop is running!
    echo.
    pause
    exit /b 1
)

echo.
echo [2/3] Waiting 12 seconds for all platform services to initialize...
timeout /t 12 /nobreak >nul

echo.
echo [3/3] Launching FinVault portals in browser...
echo.
echo Opening Student/Officer Portal...
start http://localhost:5000
echo Opening Grafana Monitoring Dashboard...
start http://localhost:3000

echo.
echo ======================================================================
echo                 FINVAULT PLATFORM ACCESS DIRECTORY
echo ======================================================================
echo.
echo   ✦ Student/Officer Web Portal : http://localhost:5000
echo   ✦ FastAPI Backend API Docs   : http://localhost:8000/docs
echo   ✦ Grafana Monitoring Console : http://localhost:3000 (admin/admin)
echo   ✦ Prometheus Metrics         : http://localhost:9090
echo   ✦ Loki Log Stream            : http://localhost:3100
echo.
echo ======================================================================
echo.
echo Press any key to stop all container services...
pause >nul

echo.
echo Stopping and cleaning docker-compose container stack...
docker-compose -f deployment/docker/docker-compose.yml down
echo.
echo All services stopped successfully.
timeout /t 3 >nul
exit
