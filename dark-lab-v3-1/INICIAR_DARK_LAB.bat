@echo off
cd /d "%~dp0"
python -m streamlit run app.py
if errorlevel 1 (
    echo.
    echo Falha ao iniciar. Instale o Python e execute:
    echo python -m pip install -r requirements.txt
    pause
)
