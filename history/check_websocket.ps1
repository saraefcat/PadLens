# Read-only local WebSocket binding audit for Input Overlay.
# Windows PowerShell 5.1 or PowerShell 7.x. Does not change OBS or firewall settings.
param([ValidateRange(1,65535)][int]$Port = 16899)
$ErrorActionPreference = 'Stop'
try {
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
} catch {
    Write-Error "TCP待受情報を取得できません: $($_.Exception.Message)"
    exit 3
}
if ($listeners.Count -eq 0) {
    Write-Warning "ポート $Port の待受がありません。Input OverlayのWebSocket設定とOBS起動状態を確認してください。"
    exit 1
}
$unsafe = $false
foreach ($listener in $listeners) {
    $ownerName = '(不明)'
    try { $ownerName = (Get-Process -Id $listener.OwningProcess -ErrorAction Stop).ProcessName }
    catch { }
    '{0}:{1}  PID={2}  Process={3}' -f $listener.LocalAddress, $listener.LocalPort, $listener.OwningProcess, $ownerName
    if ($listener.LocalAddress -notin @('127.0.0.1','::1')) {
        $unsafe = $true
        Write-Warning "ループバック以外で待受中: $($listener.LocalAddress)。LAN等から到達できるおそれがあります。"
    }
    if ($ownerName -ne '(不明)' -and $ownerName -ne 'obs64') {
        Write-Warning "待受プロセスがobs64.exeではありません。ポート競合や別プロセスの可能性があります。"
    }
}
if ($unsafe) {
    Write-Warning 'Input Overlay設定でbindを127.0.0.1に変更し、配信終了後にOBSを再起動して再確認してください。'
    exit 2
}
Write-Output 'OK: この時点では待受アドレスがループバックに限定されています。'
