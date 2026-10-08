$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$labDirectory = (Get-Location).Path
$pythonCandidates = @(
    (Join-Path $labDirectory '.venv/Scripts/python.exe'),
    (Join-Path (Split-Path -Parent $labDirectory) '.venv-lab2/Scripts/python.exe')
)
$pythonExecutable = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $pythonExecutable) { $pythonExecutable = 'python' }
Write-Host 'Mo Chrome/Edge tai http://localhost:8765/tools/record_lab2.html'
Write-Host 'Chon thu muc dataset cua du an. Ctrl+C de dung server.'
& $pythonExecutable -m http.server 8765 --bind 127.0.0.1
