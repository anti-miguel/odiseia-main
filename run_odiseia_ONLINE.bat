@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\run_public_localhostrun.ps1"
if errorlevel 1 (
  echo.
  echo [ERROR] El arranque publico fallo.
  echo Revisa logs en data\localhostrun.log y data\server_public.log
  pause
)
