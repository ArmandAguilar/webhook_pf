@echo off
cd /d "C:\Users\armand\Documents\httdocs\Forta\minigpt_apis"
call .venv\Scripts\activate.bat

@echo off

REM Ejecutar Uvicorn con recarga y puerto personalizado
uvicorn main:app --port 8005 --workers 4

REM Mantener la terminal abierta (opcional)
cmd