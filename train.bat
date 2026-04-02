@echo off
echo Installing required packages for voice model training...
pip install -r requirements.txt
echo.
echo Starting Voice Model Trainer...
python train_model.py
pause
