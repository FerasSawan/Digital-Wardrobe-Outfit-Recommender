@echo off
echo ========================================
echo Restarting Backend Server...
echo ========================================
echo.

cd ..\backend

echo Stopping any existing backend processes on port 8000...
for /f "tokens=2" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a 2>nul
)
timeout /t 2 /nobreak >nul

echo.
echo Starting backend server...
echo.

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) else (
    echo ERROR: Virtual environment not found!
    echo Please run setup_backend.bat first to create the virtual environment.
    pause
    exit /b 1
)

pause

