@echo off
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -m pip install -r requirements.txt
    py -m streamlit run app.py
    goto :eof
)

where python >nul 2>nul
if %errorlevel%==0 (
    python -m pip install -r requirements.txt
    python -m streamlit run app.py
    goto :eof
)

echo Python est introuvable. Installe Python puis relance ce fichier.
pause
