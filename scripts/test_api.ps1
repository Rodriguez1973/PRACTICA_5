param(
    [string]$ApiUrl = "http://localhost:8000",
    [string]$ApiKey = "%KhJh-yj44k[RMuJpy"
)

$ErrorActionPreference = "Stop"

Write-Host "[INFO] Probando /health en $ApiUrl"
$health = Invoke-RestMethod -Uri "$ApiUrl/health" -Method Get -TimeoutSec 15
$health | ConvertTo-Json -Depth 5

Write-Host ""
Write-Host "[INFO] Probando /generate"
$headers = @{
    "Content-Type" = "application/json"
    "X-API-Key"    = $ApiKey
}

$body = @{
    seed = "el cientifico descubrio"
    n_words = 30
    strategy = "sampling"
    temperature = 1.0
    top_k = 40
} | ConvertTo-Json

$result = Invoke-RestMethod -Uri "$ApiUrl/generate" -Method Post -Headers $headers -Body $body -TimeoutSec 30
$result | ConvertTo-Json -Depth 5

Write-Host ""
Write-Host "[OK] API funcional."
