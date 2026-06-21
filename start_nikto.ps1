# NICTO — Launch API Server + Desktop App
Write-Host "=== NICTO App Launcher ===" -ForegroundColor Green

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# Kill any existing servers
Get-Process -Name "python*" -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name "node*" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

Write-Host "[1/3] Starting API server (port 5000)..." -ForegroundColor Cyan
$apiJob = Start-Job -ScriptBlock {
    param($d) Set-Location $d
    python nikto_cli/main.py serve --no-auth --port 5000
} -ArgumentList $root
Start-Sleep -Seconds 15

# Test API
try {
    $h = Invoke-RestMethod -Uri "http://127.0.0.1:5000/health"
    Write-Host "  API: $($h.status) | brain: $($h.brain_active) | models: $($h.available_models.Count)" -ForegroundColor Green
} catch {
    Write-Host "  API: FAILED ($($_.Exception.Message))" -ForegroundColor Red
}

Write-Host "[2/3] Starting Desktop App (port 5173)..." -ForegroundColor Cyan
$env:NODE_OPTIONS="--max-old-space-size=512"
$desktopJob = Start-Job -ScriptBlock {
    param($d) Set-Location "$d/packages/nikto-desktop"
    $env:NODE_OPTIONS="--max-old-space-size=512"
    npx vite --port 5173 --host
} -ArgumentList $root
Start-Sleep -Seconds 10

# Test Desktop
try {
    $r = curl.exe -s -o nul -w "%{http_code}" http://127.0.0.1:5173
    if ($r -eq "200") { Write-Host "  Desktop: OK (port 5173)" -ForegroundColor Green }
    else { Write-Host "  Desktop: HTTP $r" -ForegroundColor Yellow }
} catch {
    Write-Host "  Desktop: FAILED" -ForegroundColor Red
}

Write-Host "[3/3] Testing model endpoints..." -ForegroundColor Cyan
$models = @("nicto_kyros", "nicto_omega", "nicto_main", "nicto_x")
foreach ($m in $models) {
    try {
        $body = "{`"message`":`"test`",`"model_id`":`"$m`"}"
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:5000/chat" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 120
        $len = $r.response.Length
        Write-Host "  $m : OK ($len chars)" -ForegroundColor Green
    } catch {
        Write-Host "  $m : ERROR ($($_.Exception.Message))" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== NICTO is RUNNING ===" -ForegroundColor Green
Write-Host "API:      http://127.0.0.1:5000" -ForegroundColor White
Write-Host "Desktop:  http://127.0.0.1:5173" -ForegroundColor White
Write-Host "CLI:      python nikto_cli/main.py <command>" -ForegroundColor White
Write-Host "Dashboard: python nikto_cli/main.py dashboard" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop both servers." -ForegroundColor Yellow

# Keep running
while ($true) {
    Start-Sleep -Seconds 10
    # Check jobs still alive
    $j = Get-Job -State Running
    if ($j.Count -lt 2) {
        Write-Host "WARNING: One or more servers stopped!" -ForegroundColor Red
        Get-Job | Format-Table Id, Name, State -AutoSize
    }
}
