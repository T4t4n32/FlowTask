@echo off
REM Arranca FlowTask (bot por polling + scheduler + panel web) en esta máquina.
REM Para que corra 24/7: pon un acceso directo a este .bat en la carpeta de Inicio
REM   (tecla Windows+R -> shell:startup)  o crea una tarea "Al iniciar sesión" en el
REM   Programador de tareas apuntando a este archivo.

cd /d "%~dp0"
call venv\Scripts\activate
REM --host 0.0.0.0 para que el celular en la misma WiFi pueda abrir el panel.
python -m uvicorn src.flowtask.main:app --host 0.0.0.0 --port 8000
