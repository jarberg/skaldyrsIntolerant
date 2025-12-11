@echo off
REM Gå til projektmappen
cd /d "C:\Users\alexh\skaldyrsIntolerant\Zantio\src"

REM Brug projektets virtuelle miljø til at køre Streamlit
"C:\Users\alexh\skaldyrsIntolerant\Zantio\.venv1\Scripts\python.exe" -m streamlit run streamlit_app.py

REM Hold vinduet åbent hvis der kommer fejl
pause
