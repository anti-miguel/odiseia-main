@echo off
setlocal
cd /d "%~dp0..\.."

set PID=
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /R /C:":8001 .*LISTENING"') do (
  set PID=%%a
)

if not defined PID (
  echo No hay proceso escuchando en 127.0.0.1:8001.
  pause
  exit /b 0
)

echo Cerrando proceso PID %PID% en puerto 8001...
taskkill /F /PID %PID%
if errorlevel 1 (
  echo No se pudo cerrar el proceso. Intenta ejecutar como Administrador.
  pause
  exit /b 1
)

echo Listo.
pause
endlocal
