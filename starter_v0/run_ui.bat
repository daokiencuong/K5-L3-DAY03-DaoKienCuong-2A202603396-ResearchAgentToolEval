@echo off
cd /d "%~dp0"
echo Starting Research Agent UI...
call .venv\Scripts\activate
streamlit run app.py
pause

