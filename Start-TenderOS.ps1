param([switch]$Development)
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskLocalRoot = Join-Path $env:LOCALAPPDATA 'TenderOS'
$taskPlatform = Join-Path $taskLocalRoot 'public-platform'
$taskPrivate = if ($env:TENDEROS_PRIVATE_ROOT) { $env:TENDEROS_PRIVATE_ROOT } else { Join-Path $env:USERPROFILE 'TenderOS-Private\private-engine' }
$taskWorker = Join-Path $taskPrivate 'worker.py'
$taskWorkerConfig = Join-Path $taskPrivate 'worker-config.json'
$taskPython = Join-Path $taskRoot 'tenderproof_os\.venv\Scripts\python.exe'
$taskNode = (Get-Command node.exe -ErrorAction Stop).Source
Push-Location -LiteralPath $taskRoot
try {
  & $taskNode (Join-Path $taskRoot 'tools\setup-local.mjs')
  if ($LASTEXITCODE -ne 0) { throw 'Local configuration failed.' }
  if (-not (Test-Path -LiteralPath (Join-Path $taskRoot 'node_modules\next\dist\bin\next'))) { throw 'Run npm install first.' }
  if (-not $Development -and -not (Test-Path -LiteralPath (Join-Path $taskRoot 'apps\web\.next\BUILD_ID'))) { throw 'Run npm run build first, or use -Development.' }
  $taskListener = Get-NetTCPConnection -State Listen -LocalPort 3414 -ErrorAction SilentlyContinue
  if (-not $taskListener) {
    $taskCommand = if ($Development) { 'dev' } else { 'start' }
    $taskNext = '"' + (Join-Path $taskRoot 'node_modules\next\dist\bin\next') + '"'
    $taskArgs = @($taskNext, $taskCommand, '--hostname', '127.0.0.1', '--port', '3414')
    $taskWeb = Start-Process -FilePath $taskNode -ArgumentList $taskArgs -WorkingDirectory (Join-Path $taskRoot 'apps\web') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskPlatform 'web-stdout.log') -RedirectStandardError (Join-Path $taskPlatform 'web-stderr.log') -PassThru
    Write-Output "TenderOS web process: $($taskWeb.Id)"
  }
  $taskReady = $false
  $taskPublicConfig = Get-Content -LiteralPath (Join-Path $taskPlatform 'config.json') -Raw | ConvertFrom-Json
  for ($taskAttempt = 0; $taskAttempt -lt 20; $taskAttempt++) {
    try {
      $taskHealth = Invoke-RestMethod -Uri 'http://127.0.0.1:3414/api/v1/health' -TimeoutSec 2
      if ($taskHealth.product -ne 'TenderOS' -or $taskHealth.protocol -ne 'pen-dev-v0.1' -or $taskHealth.platform_id -ne $taskPublicConfig.owner.id) { throw 'Port 3414 is serving a different application or installation.' }
      $taskReady = $true
      break
    } catch {
      if ($taskListener) { throw 'Existing port 3414 listener did not identify as this TenderOS installation. No node credential was sent.' }
      Start-Sleep -Milliseconds 500
    }
  }
  if (-not $taskReady) { throw 'TenderOS did not become ready. Check local web logs before starting the private node.' }
  if ((Test-Path -LiteralPath $taskWorker) -and (Test-Path -LiteralPath $taskPython)) {
    $taskModelsHelper = Join-Path $taskPrivate 'Start-Local-Models.ps1'
    if (Test-Path -LiteralPath $taskModelsHelper) { & $taskModelsHelper }
    $taskRunningWorker = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -and $_.CommandLine.Contains($taskWorker) }
    if (-not $taskRunningWorker) {
      $taskWorkerProcess = Start-Process -FilePath $taskPython -ArgumentList @('"' + $taskWorker + '"', '--config', '"' + $taskWorkerConfig + '"') -WorkingDirectory $taskPrivate -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskPlatform 'node-stdout.log') -RedirectStandardError (Join-Path $taskPlatform 'node-stderr.log') -PassThru
      Write-Output "Local private engine process: $($taskWorkerProcess.Id)"
    }
  } else { Write-Output 'Private engine is not provisioned on this computer. Portal will show engine offline.' }
  Write-Output 'Open http://127.0.0.1:3414 — PILOT_PC, free local development.'
  Write-Output ('Owner credentials: ' + (Join-Path $taskPlatform 'OWNER_LOGIN.txt'))
} finally { Pop-Location }
