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

$heartbeat = $null
if (Test-Path $HeartbeatPath) {
  try {
    $heartbeat = Get-Content -Raw $HeartbeatPath | ConvertFrom-Json
  } catch {
    $heartbeat = @{ error = "invalid heartbeat json" }
  }
}

$logs = @()
try {
  $logs = wsl.exe -d $WslDistro -- tail -n 20 "__HERMES_HOME__/runtime/logs/gateway.log"
} catch {
  $logs = @("unable to read gateway.log")
}

@{
  bootTaskState = $taskState
  wslServiceState = $serviceState
  heartbeat = $heartbeat
  recentLogs = $logs
} | ConvertTo-Json -Depth 6
