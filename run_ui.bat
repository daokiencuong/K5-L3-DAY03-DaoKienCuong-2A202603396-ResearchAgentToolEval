@echo off
cd /d "%~dp0starter_v0"
echo Starting Research Agent UI (Streamlit)...
call .venv\Scripts\activate
streamlit run app.py
pause

