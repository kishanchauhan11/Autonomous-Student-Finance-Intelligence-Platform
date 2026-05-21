@echo off
title FinVault Finance Intelligence Platform Runner
echo ======================================================================
echo          AUTONOMOUS STUDENT FINANCE INTELLIGENCE PLATFORM
echo ======================================================================
echo.

:: Get the directory of this batch file
set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo [1/3] Launching FastAPI Backend (Uvicorn)...
echo.
cd backend
start "FinVault Backend (FastAPI)" cmd /k "set PYTHONIOENCODING=utf-8&& python main.py"
cd ..

echo.
echo Waiting 6 seconds for the Backend RAG engine to initialize Qdrant index...
timeout /t 6 /nobreak >nul

echo.
echo [2/3] Launching .NET Core Frontend WebApp...
echo.
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
echo ======================================================================
echo FinVault Platform is now running!
echo - API Gateway:      http://localhost:8000
echo - Student Portal:   http://localhost:5254
echo ======================================================================
echo.
echo Keep this runner window open or press any key to close the manager.
echo (The backend and frontend terminal windows will remain running.)
echo.
pause
