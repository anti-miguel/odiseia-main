@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo   ODISEIA - ARRANQUE LOCAL
echo ==========================================
echo.

set "PY_EXE="
set "PY_ARGS="

where python >nul 2>nul
if not errorlevel 1 (
  set "PY_EXE=python"
)

if not defined PY_EXE (
  where py >nul 2>nul
  if not errorlevel 1 (
    set "PY_EXE=py"
    set "PY_ARGS=-3"
  )
)

if not defined PY_EXE (
  echo [ERROR] No se encontro Python.
  echo Instala Python 3.10+ y marca "Add python.exe to PATH".
  pause
  exit /b 1
)

echo [INFO] Usando: %PY_EXE% %PY_ARGS%

if not exist "data" mkdir "data"
set LOGFILE=data\server.log

set PID8001=
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /R /C:":8001 .*LISTENING"') do (
  set PID8001=%%a
)

if defined PID8001 (
  echo [INFO] Puerto 8001 en uso por PID %PID8001%. Cerrando proceso previo...
  taskkill /F /PID %PID8001% >nul 2>nul
  timeout /t 1 >nul
)

if not exist "data\state.json" (
  echo [1/3] Generando datos demo iniciales...
  %PY_EXE% %PY_ARGS% scripts\seed_demo_data.py > data\startup.log 2>&1
  if errorlevel 1 (
    echo [ERROR] Fallo al preparar datos demo.
    echo Revisa: data\startup.log
    type data\startup.log
    pause
    exit /b 1
  )
) else (
  echo [1/3] Usando datos existentes en data\state.json
)

echo [2/3] Verificando dependencia OpenAI...
%PY_EXE% %PY_ARGS% -c "import openai" >nul 2>nul
if errorlevel 1 (
  echo [WARN] Paquete openai no encontrado. Intentando instalar...
  %PY_EXE% %PY_ARGS% -m pip install --user openai > data\pip_openai.log 2>&1
  if errorlevel 1 (
    echo [WARN] No se pudo instalar openai automaticamente.
    echo [WARN] Odiseia seguira en modo local sin LLM.
    echo [WARN] Revisa: data\pip_openai.log
  ) else (
    %PY_EXE% %PY_ARGS% -c "import openai" >nul 2>nul
    if errorlevel 1 (
      echo [WARN] openai no esta disponible tras la instalacion.
      echo [WARN] Odiseia seguira en modo local sin LLM.
    ) else (
      echo [OK] openai instalado correctamente.
    )
  )
) else (
  echo [OK] openai ya instalado.
)

echo [3/3] Iniciando servidor en http://127.0.0.1:8001
echo Logs: %LOGFILE%
echo Pulsa Ctrl+C para parar.
echo.

echo ===== Inicio %DATE% %TIME% =====>> %LOGFILE%
set PYTHONUNBUFFERED=1
%PY_EXE% %PY_ARGS% app.py >> %LOGFILE% 2>&1

echo.
echo El servidor se ha detenido.
echo Si fue inesperado, revisa %LOGFILE%
pause
endlocal
