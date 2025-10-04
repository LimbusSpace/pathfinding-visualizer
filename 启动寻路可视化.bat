@echo off
echo Starting Pathfinding Visualizer...
echo.

python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python from: https://python.org
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -r requirements.txt

echo Starting server...
echo Browser will open: http://localhost:5000
python app.py

echo.
echo Program ended.
pause