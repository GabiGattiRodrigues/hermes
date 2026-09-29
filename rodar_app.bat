@echo off
REM Abre o app do Hermes no navegador
cd /d "%~dp0"
set PYTHONUTF8=1
call .venv\Scripts\activate.bat
streamlit run app\app.py
