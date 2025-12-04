@echo off
setlocal

REM === Static settings ===
set "PGHOST=localhost"
set "PGPORT=5432"
set "DB_NAME=wardrobe_DB"

echo ================================
echo  PostgreSQL DB creation script
echo ================================
echo.

REM === Ask for username ===
set /p PGUSER=Enter PostgreSQL username: 

REM === Ask for password (NOTE: visible as you type) ===
set /p PGPASSWORD=Enter password for %PGUSER%: 

echo.
echo Using host: %PGHOST%
echo Using port: %PGPORT%
echo Target database: %DB_NAME%
echo.

REM === Check that psql is available ===
where psql >nul 2>&1
if errorlevel 1 (
    echo [ERROR] psql command not found. Make sure PostgreSQL "bin" directory is in your PATH.
    echo Example: C:\Program Files\PostgreSQL\16\bin
    goto :EOF
)

REM === Check if database already exists ===
echo Checking if database "%DB_NAME%" exists...
psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -tAc "SELECT 1 FROM pg_database WHERE datname='%DB_NAME%';" | find "1" >nul 2>&1

if %errorlevel%==0 (
    echo.
    echo Database "%DB_NAME%" already exists. No action taken.
    goto :EOF
)

REM === Create the database ===
echo.
echo Creating database "%DB_NAME%"...
psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -c "CREATE DATABASE \"%DB_NAME%\";"

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to create database "%DB_NAME%".
    goto :EOF
)

echo.
echo Database "%DB_NAME%" created successfully.

endlocal