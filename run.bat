@echo off
REM Arranca FlowTask (bot por polling + scheduler + panel web) en esta máquina.
REM Para que corra 24/7: pon un acceso directo a este .bat en la carpeta de Inicio
REM   (tecla Windows+R -> shell:startup)  o crea una tarea "Al iniciar sesión" en el
REM   Programador de tareas apuntando a este archivo.

cd /d "%~dp0"
call venv\Scripts\activate
python -m uvicorn src.flowtask.main:app --host 127.0.0.1 --port 8000
