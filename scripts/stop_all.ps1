$ErrorActionPreference = "SilentlyContinue"

Write-Host "[INFO] Cerrando procesos comunes de PRACTICA_4/PRACTICA_5..."

Get-Process -Name "python","python3","uvicorn" | ForEach-Object {
    try {
        Stop-Process -Id $_.Id -Force
        Write-Host "[OK] Proceso detenido: $($_.ProcessName) (PID $($_.Id))"
    } catch {
        # Ignorar errores de permisos/proceso finalizado
    }
}

Write-Host "[INFO] Si tenias otras tareas Python abiertas, revisa manualmente."
