# Lalobot — instalación e inicio en Windows (PowerShell)
# Uso:  powershell -ExecutionPolicy Bypass -File setup_windows.ps1
$ErrorActionPreference = "Stop"

Write-Host "==> [1/4] Trayendo submodulos (sherlock, awesome-osint...)" -ForegroundColor Cyan
git submodule update --init --recursive

Write-Host "==> [2/4] Creando entorno virtual" -ForegroundColor Cyan
if (-not (Test-Path "venv")) { python -m venv venv }

Write-Host "==> [3/4] Instalando dependencias (puede tardar)" -ForegroundColor Cyan
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "==> [4/4] Iniciando servidor Lalobot" -ForegroundColor Green
Write-Host "    Abri en el navegador:  http://localhost:5001" -ForegroundColor Yellow
venv\Scripts\python.exe main.py web
