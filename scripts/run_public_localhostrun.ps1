param()

Set-Location -Path (Join-Path $PSScriptRoot '..')

$PORT = 8001
$APP_LOG = 'data/server_public.log'
$LR_LOG = 'data/localhostrun.log'
$PUBLIC_URL_FILE = 'data/public_url.txt'
$PUBLIC_QR_FILE = 'data/public_qr_url.txt'

New-Item -ItemType Directory -Force -Path 'data' | Out-Null
Remove-Item -ErrorAction SilentlyContinue $APP_LOG, $LR_LOG, $PUBLIC_URL_FILE, $PUBLIC_QR_FILE

Write-Host '=========================================='
Write-Host '  ODISEIA - PUBLIC HOST (LOCALHOST.RUN)'
Write-Host '=========================================='
Write-Host ("Script: {0}" -f $MyInvocation.MyCommand.Path)
Write-Host ("Carpeta: {0}" -f (Get-Location))
Write-Host ''

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Host '[ERROR] Python no esta en PATH.'
  Read-Host 'Pulsa Enter para salir'
  exit 1
}
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
  Write-Host '[ERROR] ssh no esta en PATH (OpenSSH Client).'
  Read-Host 'Pulsa Enter para salir'
  exit 1
}

if (-not (Test-Path 'data/state.json')) {
  Write-Host '[1/3] Generando datos demo iniciales...'
  python scripts/seed_demo_data.py *> data/startup.log
  if ($LASTEXITCODE -ne 0) {
    Write-Host '[ERROR] No se pudo crear data/state.json'
    Get-Content data/startup.log -ErrorAction SilentlyContinue
    Read-Host 'Pulsa Enter para salir'
    exit 1
  }
}
else {
  Write-Host '[1/3] Usando datos existentes en data/state.json'
}

Write-Host ("[2/3] Iniciando backend local en http://127.0.0.1:{0}" -f $PORT)
Write-Host ("Logs backend: {0}" -f $APP_LOG)
$line = netstat -ano | Select-String (":{0} .*LISTENING" -f $PORT) | Select-Object -First 1
if ($line) {
  $portPid = ($line -split '\s+')[-1]
  if ($portPid) { taskkill /F /PID $portPid *> $null }
}
$cwd = (Get-Location).Path
Start-Process cmd.exe -ArgumentList '/k', ("cd /d `"{0}`" && set PYTHONUNBUFFERED=1 && python app.py >> {1} 2>&1" -f $cwd, $APP_LOG)
Start-Sleep -Seconds 2

Write-Host '[3/3] Abriendo tunel publico con localhost.run...'
Write-Host ("Logs tunel: {0}" -f $LR_LOG)
Start-Process cmd.exe -ArgumentList '/k', ("cd /d `"{0}`" && call scripts\internal_bat\run_localhostrun_retry.bat {1}" -f $cwd, $PORT)

$url = $null
for ($i = 0; $i -lt 60; $i++) {
  if (Test-Path $LR_LOG) {
    $txt = Get-Content -Raw -ErrorAction SilentlyContinue $LR_LOG
    if ($txt) {
      $m = [regex]::Matches($txt, 'https://[A-Za-z0-9.-]+\.lhr\.life')
      if ($m.Count -gt 0) {
        $url = $m[$m.Count - 1].Value
        break
      }
    }
  }
  Start-Sleep -Seconds 1
}

if (-not $url) {
  Write-Host '[ERROR] No se detecto URL publica automaticamente.'
  Write-Host 'Abre data/localhostrun.log y busca una URL https://xxxxx.lhr.life'
  Read-Host 'Pulsa Enter para salir'
  exit 1
}

Set-Content -Path $PUBLIC_URL_FILE -Value $url -Encoding ASCII
$qrUrl = "https://api.qrserver.com/v1/create-qr-code/?size=320x320&data=$url"
Set-Content -Path $PUBLIC_QR_FILE -Value $qrUrl -Encoding ASCII

$url | Set-Clipboard

Write-Host ''
Write-Host '[OK] URL publica detectada:'
Write-Host $url
Write-Host ("[OK] URL copiada al portapapeles y guardada en {0}" -f $PUBLIC_URL_FILE)
Write-Host ("[OK] QR URL guardada en {0}" -f $PUBLIC_QR_FILE)
Write-Host ''
Write-Host 'Nota: ignora el QR ASCII en localhostrun.log.'
Write-Host 'Usa data/public_qr_url.txt para abrir un QR limpio.'
Write-Host ''
Write-Host 'Si quieres cerrar todo:'
Write-Host '1) cierra las ventanas "Odiseia Backend" y "Odiseia Tunnel"'
Write-Host '2) o ejecuta scripts\internal_bat\stop_odiseia.bat'
Read-Host 'Pulsa Enter para salir'
