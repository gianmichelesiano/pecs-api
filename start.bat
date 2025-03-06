@echo off
call .\.venv\Scripts\activate
python -m fastapi dev --port 5000 app/main.py
pause