@echo off
echo Setting up backend...

call .\setup_db.bat
cd ..\backend


echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Backend setup complete!
pause

