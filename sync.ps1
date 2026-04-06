# Script de sincronización automática (Robustecido V2)
$gitPath = "C:\Program Files\Git\bin\git.exe"
if (-not (Test-Path $gitPath)) {
    $gitPath = "git" 
}

# Obtener rama actual
$currentBranch = (& $gitPath branch --show-current).Trim()
Write-Host "Sincronizando en rama: $currentBranch" -ForegroundColor Cyan

# Añadir todos los archivos (respetando .gitignore)
& $gitPath add .

# Commit con timestamp y versión
$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
& $gitPath commit -m "Auto-deploy [$currentBranch] - Version 2026.04.008 - $timestamp"

# Push a la rama actual
& $gitPath push origin $currentBranch

Write-Host "¡Pokedex sincronizada con GitHub con éxito en branch $currentBranch! 🚀" -ForegroundColor Green
