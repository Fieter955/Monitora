[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateScript({
        $parsed = $null
        [System.Net.IPAddress]::TryParse($_, [ref]$parsed) -and
            $parsed.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork
    })]
    [string]$Target,

    [string]$LabNetwork = "192.168.250.0"
)

$ErrorActionPreference = "Continue"
$projectDir = Split-Path -Parent $PSScriptRoot

function Write-Check {
    param([string]$Name, [bool]$Passed, [string]$Detail)
    $status = if ($Passed) { "LULUS" } else { "PERIKSA" }
    $color = if ($Passed) { "Green" } else { "Yellow" }
    Write-Host ("[{0}] {1}: {2}" -f $status, $Name, $Detail) -ForegroundColor $color
}

Write-Host "Preflight lab LibreNMS" -ForegroundColor Cyan
Write-Host ("Target: {0}" -f $Target)
Write-Host ""

$routeOutput = route.exe print -4 | Out-String
$matchingRoutes = @($routeOutput -split "`r?`n" | Where-Object {
    $_ -match [regex]::Escape($LabNetwork)
})
$routeDetail = if ($matchingRoutes.Count -eq 1) {
    "Satu rute yang cocok ditemukan. Pastikan rute ini menunjuk ke Ethernet lab, bukan Wi-Fi/VPN."
} elseif ($matchingRoutes.Count -gt 1) {
    "Lebih dari satu rute cocok. Periksa kemungkinan konflik dengan Wi-Fi atau VPN."
} else {
    "Belum ada rute eksplisit; sambungkan Ethernet dan atur IP statis terlebih dahulu."
}
Write-Check "Rute lab" ($matchingRoutes.Count -eq 1) $routeDetail

Push-Location $projectDir
try {
    $composeServices = docker compose ps --services --filter status=running 2>&1
    $dockerOk = $LASTEXITCODE -eq 0
    $librenmsRunning = $dockerOk -and ($composeServices -contains "librenms")
    $composeDetail = if ($dockerOk) { "Perintah Compose dapat dijalankan." } else { $composeServices -join " " }
    $librenmsDetail = if ($librenmsRunning) { "Service librenms sedang berjalan." } else { "Docker tidak tersedia atau service librenms belum berjalan." }
    Write-Check "Docker Compose" $dockerOk $composeDetail
    Write-Check "Container LibreNMS" $librenmsRunning $librenmsDetail

    $windowsPing = Test-Connection -ComputerName $Target -Count 2 -Quiet -ErrorAction SilentlyContinue
    $windowsPingDetail = if ($windowsPing) { "Target dapat dijangkau melalui host." } else { "Periksa IP, subnet, kabel, VLAN, dan firewall perangkat." }
    Write-Check "Ping dari Windows" $windowsPing $windowsPingDetail

    if ($librenmsRunning) {
        $containerPingOutput = docker compose exec -T librenms ping -c 3 -W 2 $Target 2>&1
        $containerPing = $LASTEXITCODE -eq 0
        $containerPingDetail = if ($containerPing) { "Jalur Docker Desktop ke perangkat fisik berfungsi." } else { $containerPingOutput -join " " }
        Write-Check "Ping dari container LibreNMS" $containerPing $containerPingDetail

        $validationOutput = docker compose exec -T --user librenms librenms php /opt/librenms/validate.php 2>&1
        $validationOk = $LASTEXITCODE -eq 0
        $validationDetail = if ($validationOk) { "Validator LibreNMS selesai tanpa exit error." } else { "Jalankan validator manual dan periksa detail keluarannya." }
        Write-Check "Validasi LibreNMS" $validationOk $validationDetail
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Catatan: ping tidak membuktikan SNMP UDP 161." -ForegroundColor Cyan
Write-Host "Lanjutkan dari wizard Perangkat dengan kredensial read-only, lalu pilih 'Simpan & temukan port'."
