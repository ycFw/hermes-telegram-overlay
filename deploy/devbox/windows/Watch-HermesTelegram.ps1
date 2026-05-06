param(
  [string]$WslDistro = "__WSL_DISTRO__",
  [string]$ServiceName = "__SERVICE_NAME__",
  [string]$HeartbeatPath = "__HEARTBEAT_PATH__",
  [string]$BootTaskName = "__BOOT_TASK_NAME__"
)

$taskState = $null
try {
  $taskState = (Get-ScheduledTask -TaskName $BootTaskName -ErrorAction Stop).State
} catch {
  $taskState = "missing"
}

$serviceState = "unknown"
try {
  $serviceState = (wsl.exe -d $WslDistro -- systemctl --user is-active $ServiceName).Trim()
} catch {
  $serviceState = "error"
}

if ($serviceState -ne "active") {
  wsl.exe -d $WslDistro -- systemctl --user restart $ServiceName | Out-Null
  Start-Sleep -Seconds 2
  try {
    $serviceState = (wsl.exe -d $WslDistro -- systemctl --user is-active $ServiceName).Trim()
  } catch {
    $serviceState = "error"
  }
}

$heartbeat = @{
  timestamp = (Get-Date).ToString("o")
  bootTaskState = $taskState
  wslServiceState = $serviceState
}

$heartbeatDir = Split-Path -Parent $HeartbeatPath
New-Item -ItemType Directory -Force -Path $heartbeatDir | Out-Null
$heartbeat | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 -Path $HeartbeatPath
