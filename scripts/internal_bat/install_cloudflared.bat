@echo off
setlocal
cd /d "%~dp0..\.."

echo ==========================================
echo   INSTALAR CLOUDFLARED (WINDOWS)
echo ==========================================
echo.

where winget >nul 2>nul
if errorlevel 1 (
  echo [ERROR] winget no esta disponible.
  echo Instala cloudflared manualmente:
  echo https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
  pause
  exit /b 1
)

echo Instalando cloudflared con winget...
winget install -e --id Cloudflare.cloudflared
if errorlevel 1 (
  echo.
  echo [ERROR] No se pudo instalar cloudflared con winget.
  echo Prueba instalacion manual:
  echo https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
  pause
  exit /b 1
)

echo.
echo Instalacion completada.
echo Verificando...
where cloudflared
if errorlevel 1 (
  echo [WARN] cloudflared instalado pero no detectado en PATH.
  echo Cierra y abre la terminal, o reinicia sesion de Windows.
) else (
  echo [OK] cloudflared disponible.
)
pause
endlocal
