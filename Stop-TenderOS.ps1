$ErrorActionPreference = 'Stop'
$taskNext = Join-Path $PSScriptRoot 'node_modules\next\dist\bin\next'
$taskPrivateRoot = if ($env:TENDEROS_PRIVATE_ROOT) { $env:TENDEROS_PRIVATE_ROOT } else { Join-Path $env:USERPROFILE 'TenderOS-Private\private-engine' }
$taskPrivateWorker = Join-Path $taskPrivateRoot 'worker.py'
$taskProcesses = @(Get-CimInstance Win32_Process)
$taskRoots = @($taskProcesses | Where-Object {
  $_.CommandLine -and (
    ($_.Name -eq 'node.exe' -and $_.CommandLine.Contains($taskNext) -and $_.CommandLine.Contains('3414')) -or
    ($_.Name -eq 'python.exe' -and $_.CommandLine.Contains($taskPrivateWorker))
  )
})
foreach ($taskRootProcess in $taskRoots) {
  $taskOwnedIds = @([uint32]$taskRootProcess.ProcessId)
  do {
    $taskChildren = @($taskProcesses | Where-Object { $taskOwnedIds -contains $_.ParentProcessId -and $taskOwnedIds -notcontains $_.ProcessId })
    $taskOwnedIds += @($taskChildren | ForEach-Object { [uint32]$_.ProcessId })
  } while ($taskChildren.Count -gt 0)
  [array]::Reverse($taskOwnedIds)
  foreach ($taskProcessId in $taskOwnedIds) { Stop-Process -Id $taskProcessId -ErrorAction SilentlyContinue }
}
Write-Output 'Stopped TenderOS web processes for this checkout and its external worker. Stored records are preserved.'
