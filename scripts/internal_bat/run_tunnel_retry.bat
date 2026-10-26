@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0..\.."

if "%~1"=="" (
  echo Uso: run_tunnel_retry.bat ^<port^>
  exit /b 1
)

set PORT=%~1
set TUNNEL_LOG=data\cloudflared.log

for /f "delims=" %%p in ('where cloudflared') do (
  set "CF_EXE=%%p"
  goto :cf_ok
)

echo [ERROR] No se encontro cloudflared en PATH.
echo Ejecuta scripts\internal_bat\install_cloudflared.bat o instala cloudflared manualmente.
exit /b 1

:cf_ok
if not exist "%TUNNEL_LOG%" (
  break > "%TUNNEL_LOG%"
)

echo ==========================================
echo   ODISEIA TUNNEL - AUTO RETRY
echo ==========================================
echo Puerto local: %PORT%
echo Log: %TUNNEL_LOG%
echo Cloudflared: %CF_EXE%
echo.
echo No cierres esta ventana mientras dure la demo.
echo Si Cloudflare falla temporalmente, el tunel se reintentara solo.
echo.

:loop
echo ===== Intento %DATE% %TIME% =====>> "%TUNNEL_LOG%"
"%CF_EXE%" tunnel --url http://127.0.0.1:%PORT% >> "%TUNNEL_LOG%" 2>&1
if errorlevel 1 (
  for /f "usebackq delims=" %%l in (`powershell -NoProfile -Command "$p='%TUNNEL_LOG%'; if(Test-Path $p){ Get-Content $p -Tail 1 }"`) do set "LAST_LINE=%%l"
  if defined LAST_LINE echo [WARN] Ultimo error: !LAST_LINE!
)
echo.
echo [WARN] El tunel se detuvo o fallo. Reintentando en 8 segundos...
timeout /t 8 >nul
goto :loop
