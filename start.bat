@echo off
title Sistema de Gestion de Panaderia - TFG UNIGRAN
echo ========================================================
echo   SISTEMA DE GESTION DE PANADERIA (TFG UNIGRAN)
echo   Iniciando servidor de desarrollo...
echo ========================================================

if not exist venv (
    echo Creando entorno virtual Python...
    python -m venv venv
    call .\venv\Scripts\activate.bat
    pip install -r requirements.txt
    python seed_data.py
) else (
    call .\venv\Scripts\activate.bat
)

echo Abriendo navegador en http://127.0.0.1:8000 ...
start http://127.0.0.1:8000

echo Iniciando FastAPI con Uvicorn...
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause
