[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$MonitoringServer,
    [string]$ServiceIncludePattern = "windows_exporter",
    [string]$Version = "0.31.8"
)

$ErrorActionPreference = "Stop"
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Jalankan PowerShell sebagai Administrator."
}
if ($ServiceIncludePattern -notmatch '^[A-Za-z0-9_|().*?+-]+$') {
    throw "ServiceIncludePattern berisi karakter yang tidak didukung."
}

$fileName = "windows_exporter-$Version-amd64.msi"
$download = Join-Path $env:TEMP $fileName
$url = "https://github.com/prometheus-community/windows_exporter/releases/download/v$Version/$fileName"
Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $download

if ($Version -eq "0.31.8") {
    $expected = "0aadce6afb20182b678bfca9e8f2e8464ef48c469b28b4cf02e99d82158f5d40"
    $actual = (Get-FileHash -LiteralPath $download -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $expected) { throw "Checksum windows_exporter tidak cocok." }
}

$arguments = @(
    "/i", $download, "/qn", "/norestart",
    "ENABLED_COLLECTORS=cpu,logical_disk,memory,net,os,service,system",
    "LISTEN_PORT=9182",
    "EXTRA_FLAGS=--collector.service.include=$ServiceIncludePattern"
)
$process = Start-Process msiexec.exe -ArgumentList $arguments -Wait -PassThru
if ($process.ExitCode -ne 0) { throw "Instalasi windows_exporter gagal: $($process.ExitCode)" }

Get-NetFirewallRule -DisplayName "Monitora windows_exporter" -ErrorAction SilentlyContinue | Remove-NetFirewallRule
New-NetFirewallRule -DisplayName "Monitora windows_exporter" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 9182 -RemoteAddress $MonitoringServer | Out-Null
Write-Host "windows_exporter aktif. Tambahkan target $($env:COMPUTERNAME):9182 ke Monitora."
