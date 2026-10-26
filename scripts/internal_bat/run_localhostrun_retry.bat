@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0..\.."

if "%~1"=="" (
  echo Uso: run_localhostrun_retry.bat ^<port^>
  exit /b 1
)

set PORT=%~1
set LR_LOG=data\localhostrun.log
set SSH_KEY=%LOCALHOSTRUN_SSH_KEY%
set SUBDOMAIN=%LOCALHOSTRUN_SUBDOMAIN%
set SSH_TARGET=%LOCALHOSTRUN_SSH_TARGET%

if not exist data (
  mkdir data >nul 2>nul
)
if not exist "%LR_LOG%" (
  break > "%LR_LOG%"
)

if defined SUBDOMAIN (
  echo %SUBDOMAIN% | findstr /r "\." >nul
  if errorlevel 1 (
    echo [WARN] LOCALHOSTRUN_SUBDOMAIN no es FQDN: %SUBDOMAIN%
    echo [WARN] Se ignorara SUBDOMAIN y se usara URL dinamica.
    set "SUBDOMAIN="
  )
)

if defined SSH_KEY (
  if not exist "%SSH_KEY%" (
    echo [WARN] LOCALHOSTRUN_SSH_KEY no existe en este PC: %SSH_KEY%
    set "SSH_KEY="
  )
)

if not defined SSH_KEY (
  if exist "%USERPROFILE%\.ssh\id_ed25519_localhostrun" (
    set "SSH_KEY=%USERPROFILE%\.ssh\id_ed25519_localhostrun"
  ) else if exist "%USERPROFILE%\.ssh\id_ed25519" (
    set "SSH_KEY=%USERPROFILE%\.ssh\id_ed25519"
  ) else if exist "%USERPROFILE%\.ssh\id_rsa" (
    set "SSH_KEY=%USERPROFILE%\.ssh\id_rsa"
  )
)

echo ==========================================
echo   ODISEIA TUNNEL - LOCALHOST.RUN RETRY
echo ==========================================
echo Puerto local: %PORT%
echo Log: %LR_LOG%
if not defined SSH_TARGET (
  if defined SSH_KEY (
    set "SSH_TARGET=plan@localhost.run"
  ) else (
    set "SSH_TARGET=nokey@localhost.run"
  )
)
if defined SSH_KEY (
  if /I "%SSH_TARGET%"=="nokey@localhost.run" set "SSH_TARGET=plan@localhost.run"
)
echo Usuario SSH: %SSH_TARGET%
if defined SUBDOMAIN (
  echo Subdominio solicitado: %SUBDOMAIN%
)
if defined SSH_KEY (
  echo SSH key personalizada: %SSH_KEY%
 ) else (
  echo SSH key personalizada: (ninguna, modo anonimo)
)
echo.
echo No cierres esta ventana mientras dure la demo.
echo Si el tunel se cae, se reconectara automaticamente.
echo.

:loop
echo ===== Intento %DATE% %TIME% =====>> "%LR_LOG%"

if defined SUBDOMAIN (
  set "REMOTE_SPEC=%SUBDOMAIN%:80:127.0.0.1:%PORT%"
) else (
  set "REMOTE_SPEC=80:127.0.0.1:%PORT%"
)

if defined SSH_KEY (
  ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes -o StrictHostKeyChecking=accept-new -i "%SSH_KEY%" -R %REMOTE_SPEC% %SSH_TARGET% >> "%LR_LOG%" 2>&1
) else (
  ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes -o StrictHostKeyChecking=accept-new -R %REMOTE_SPEC% %SSH_TARGET% >> "%LR_LOG%" 2>&1
)

echo.
echo [WARN] El tunel se detuvo. Reintentando en 8 segundos...
echo [WARN] El tunel se detuvo. Reintentando en 8 segundos...>> "%LR_LOG%"
timeout /t 8 >nul
goto :loop
