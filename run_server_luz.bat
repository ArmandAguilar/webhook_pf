@echo off
cd /d "C:\Users\Proyectos\Documents\Proyectos\webhook_pf"
call .venv\Scripts\activate.bat

@echo off

REM Ejecutar Uvicorn con recarga y puerto personalizado
uvicorn main:app --port 8005 --workers 4

REM Mantener la terminal abierta (opcional)
cmd