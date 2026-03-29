param(
    [string]$ApiKey = "%KhJh-yj44k[RMuJpy",
    [int]$ApiPort = 8000,
    [int]$WebPort = 8080,
    [string]$PythonCommand = "python"
)

$ErrorActionPreference = "Stop"

$practica5 = Split-Path -Parent $PSScriptRoot
$modeloPath    = Join-Path $practica5 "modelo"
$tokenizerPath = Join-Path $practica5 "tokenizer"
$venvPath      = Join-Path $practica5 ".venv"
# python3.10 on Windows can place python3.10.exe instead of python.exe in the venv
function Get-VenvPython {
    param([string]$VenvPath)
    $candidates = @("python.exe", "python3.10.exe", "python3.11.exe", "python3.exe")
    foreach ($name in $candidates) {
        $p = Join-Path $VenvPath "Scripts\$name"
        if (Test-Path $p) { return $p }
    }
    throw "No se encontro un ejecutable Python en: $VenvPath\Scripts\"
}
$pythonExe = $null  # will be resolved after venv creation
$apiDepsLegacy = @(
    "tensorflow==2.21.0",
    "numpy==1.26.4",
    "fastapi==0.111.0",
    "uvicorn[standard]==0.30.1",
    "pydantic==2.7.1",
    "slowapi==0.1.9",
    "python-dotenv==1.0.1"
)
$apiDepsPy313 = @(
    "tensorflow==2.21.0",
    "numpy>=2.1.0,<3.0.0",
    "fastapi>=0.115.0,<1.0.0",
    "uvicorn[standard]>=0.35.0,<1.0.0",
    "pydantic>=2.11.0,<3.0.0",
    "slowapi==0.1.9",
    "python-dotenv==1.0.1"
)

function Get-PythonCommandLine {
    param([string]$CommandText)

    $commandInfo = Get-Command $CommandText -ErrorAction SilentlyContinue
    if ($commandInfo) {
        return $CommandText
    }

    if (Test-Path $CommandText) {
        return ('"{0}"' -f $CommandText)
    }

    throw "No se encontro el interprete Python indicado: $CommandText"
}

$pythonBootstrap = Get-PythonCommandLine -CommandText $PythonCommand

Write-Host "[INFO] PRACTICA_5 path: $practica5"
Write-Host "[INFO] Modelo path: $modeloPath"
Write-Host "[INFO] Tokenizer path: $tokenizerPath"
Write-Host "[INFO] Python base command: $PythonCommand"

if (-not (Test-Path (Join-Path $modeloPath "model_final.keras"))) {
    throw "No se encontro el modelo en PRACTICA_5\modelo\model_final.keras"
}

if (-not (Test-Path (Join-Path $tokenizerPath "tokenizer.json"))) {
    throw "No se encontro el tokenizer en PRACTICA_5\tokenizer\tokenizer.json"
}

if (-not (Test-Path (Join-Path $practica5 "app.py"))) {
    throw "No se encontro la API en PRACTICA_5\app.py"
}

if (-not (Test-Path (Join-Path $practica5 "train.py"))) {
    throw "No se encontro train.py en PRACTICA_5\train.py"
}

if (-not (Test-Path (Join-Path $practica5 "model.py"))) {
    throw "No se encontro model.py en PRACTICA_5\model.py"
}

# Check if venv already has a usable python executable
$existingPython = $null
try { $existingPython = Get-VenvPython -VenvPath $venvPath } catch {}

if (-not $existingPython) {
    Write-Host "[INFO] Creando entorno virtual en PRACTICA_5..."
    $pythonExePath = (Get-Command $PythonCommand).Source
    & $pythonExePath -m venv "$venvPath"
    if ($LASTEXITCODE -ne 0) { throw "Fallo la creacion del entorno virtual." }
    $existingPython = Get-VenvPython -VenvPath $venvPath
}
$pythonExe = $existingPython
Write-Host "[INFO] Usando Python del venv: $pythonExe"

Write-Host "[INFO] Detectando version de Python del entorno..."
Push-Location $practica5
& $pythonExe -m pip install --upgrade pip
$pythonVersion = (& $pythonExe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')").Trim()
Write-Host "[INFO] Python detectado en .venv: $pythonVersion"

if ($pythonVersion -eq "3.13") {
    Write-Host "[INFO] Python 3.13 detectado. Instalando dependencias compatibles para el API..."
    & $pythonExe -m pip install $apiDepsPy313
} else {
    Write-Host "[INFO] Instalando dependencias para el API local..."
    & $pythonExe -m pip install $apiDepsLegacy
}
Pop-Location

$apiCommand = @"
`$env:MODEL_PATH='modelo/model_final.keras'
`$env:TOKENIZER_PATH='tokenizer/tokenizer.json'
`$env:API_KEY='$ApiKey'
`$env:RATE_LIMIT='10'
Set-Location '$practica5'
& '$pythonExe' -m uvicorn app:app --host 0.0.0.0 --port $ApiPort
"@

$webCommand = @"
Set-Location '$practica5\web_client'
$pythonBootstrap -m http.server $WebPort
"@

Write-Host "[INFO] Abriendo terminal para API REST..."
Start-Process pwsh -ArgumentList "-NoExit", "-Command", $apiCommand | Out-Null

Start-Sleep -Seconds 3

Write-Host "[INFO] Abriendo terminal para cliente web..."
Start-Process pwsh -ArgumentList "-NoExit", "-Command", $webCommand | Out-Null

Start-Sleep -Seconds 2

Write-Host "[INFO] Probando endpoint /health..."
try {
    $health = Invoke-RestMethod -Uri "http://localhost:$ApiPort/health" -Method Get -TimeoutSec 10
    Write-Host "[OK] API levantada: status=$($health.status), model_loaded=$($health.model_loaded), tokenizer_loaded=$($health.tokenizer_loaded)"
} catch {
    Write-Warning "No se pudo validar /health aun. Espera unos segundos y prueba de nuevo."
}

$webUrl = "http://localhost:$WebPort"
Write-Host "[INFO] Abriendo navegador en $webUrl"
Start-Process $webUrl | Out-Null

Write-Host ""
Write-Host "Listo."
Write-Host "1) API:      http://localhost:$ApiPort/docs"
Write-Host "2) Web app:  http://localhost:$WebPort"
Write-Host "3) API Key:  $ApiKey"
