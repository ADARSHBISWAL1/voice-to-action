@echo off
cd /d "%~dp0"
pip install -r requirements.txt -q
echo Starting server... Open http://127.0.0.1:5000 in Chrome or Edge.
python app.py
pause
