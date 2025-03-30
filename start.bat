@echo off
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 5000
pause
