[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    if (-not (Test-Path .env)) { throw "Salin .env.example menjadi .env terlebih dahulu." }
    $environment = Get-Content .env -ErrorAction Stop
    foreach ($name in "VSPHERE_URL", "VSPHERE_USERNAME", "VSPHERE_PASSWORD") {
        $line = $environment | Where-Object { $_ -match "^$name=" } | Select-Object -Last 1
        if (-not $line -or $line -match 'replace-|example\.local') {
            throw "$name belum diisi dengan nilai ESXi/vCenter yang sebenarnya."
        }
    }

    docker compose --profile vmware run --rm telegraf-vsphere --test --test-wait 30
    if ($LASTEXITCODE -ne 0) {
        throw "Preflight vSphere gagal. Target Prometheus tidak diaktifkan."
    }
    Copy-Item infra/prometheus/file_sd/vmware.yml.disabled infra/prometheus/file_sd/vmware.yml -Force
    docker compose --profile vmware up -d telegraf-vsphere prometheus
    if ($LASTEXITCODE -ne 0) { throw "Kolektor VMware gagal dijalankan." }
    Write-Host "Kolektor VMware aktif dan tersedia untuk Prometheus."
} finally {
    Pop-Location
}
