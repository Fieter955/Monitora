[CmdletBinding()]
param(
    [string]$InstallRoot = "C:\Program Files\Monitora",
    [string]$DataRoot = "C:\ProgramData\Monitora",
    [string]$PostgresSuperPassword,
    [string]$DatabasePassword,
    [string]$AdminUsername = "admin",
    [string]$AdminPassword,
    [string]$SnmpCommunity = "public",
    [int]$HttpPort = 8080
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$repoRoot = Split-Path -Parent $PSScriptRoot

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Jalankan PowerShell sebagai Administrator."
    }
}

function New-RandomSecret([int]$Bytes = 32) {
    $buffer = New-Object byte[] $Bytes
    [Security.Cryptography.RandomNumberGenerator]::Fill($buffer)
    return [Convert]::ToHexString($buffer).ToLowerInvariant()
}

function Install-WingetPackage([string]$Id) {
    $installed = winget list --id $Id --exact --accept-source-agreements 2>$null
    if ($LASTEXITCODE -eq 0 -and ($installed -join "`n") -match [regex]::Escape($Id)) { return }
    winget install --id $Id --exact --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
    if ($LASTEXITCODE -ne 0) { throw "Gagal memasang paket $Id melalui winget." }
}

function Install-PrometheusArchive([string]$Project, [string]$Version, [string]$ArchiveName) {
    $destination = Join-Path $DataRoot "packages\$Project"
    if (Test-Path (Join-Path $destination "$Project.exe")) { return $destination }
    $tempArchive = Join-Path $env:TEMP $ArchiveName
    $baseUrl = "https://github.com/prometheus/$Project/releases/download/v$Version"
    Invoke-WebRequest -UseBasicParsing -Uri "$baseUrl/$ArchiveName" -OutFile $tempArchive
    $checksums = (Invoke-WebRequest -UseBasicParsing -Uri "$baseUrl/sha256sums.txt").Content
    $escapedName = [regex]::Escape($ArchiveName)
    $match = [regex]::Match($checksums, "(?im)^([a-f0-9]{64})\s+\*?$escapedName$")
    if (-not $match.Success) { throw "Checksum resmi $ArchiveName tidak ditemukan." }
    $actual = (Get-FileHash -LiteralPath $tempArchive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $match.Groups[1].Value.ToLowerInvariant()) {
        throw "Checksum $ArchiveName tidak cocok."
    }
    $extractRoot = Join-Path $env:TEMP "monitora-$Project-$Version"
    if (Test-Path $extractRoot) { Remove-Item -LiteralPath $extractRoot -Recurse -Force }
    Expand-Archive -LiteralPath $tempArchive -DestinationPath $extractRoot -Force
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    $source = Get-ChildItem -LiteralPath $extractRoot -Directory | Select-Object -First 1
    Copy-Item -Path (Join-Path $source.FullName "*") -Destination $destination -Recurse -Force
    return $destination
}

function Find-Executable([string]$Name, [string[]]$Candidates) {
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    foreach ($candidate in $Candidates) {
        $match = Get-ChildItem -Path $candidate -Filter $Name -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($match) { return $match.FullName }
    }
    throw "$Name tidak ditemukan setelah instalasi. Buka PowerShell baru lalu jalankan installer kembali."
}

function Install-WrappedService(
    [string]$Id,
    [string]$DisplayName,
    [string]$Executable,
    [string]$Arguments,
    [string]$WorkingDirectory,
    [string]$WinSw
) {
    $serviceRoot = Join-Path $DataRoot "services\$Id"
    New-Item -ItemType Directory -Path $serviceRoot -Force | Out-Null
    $wrapper = Join-Path $serviceRoot "$Id.exe"
    Copy-Item -LiteralPath $WinSw -Destination $wrapper -Force
    $xml = @"
<service>
  <id>$Id</id>
  <name>$DisplayName</name>
  <description>Komponen layanan Monitora</description>
  <executable>$Executable</executable>
  <arguments>$Arguments</arguments>
  <workingdirectory>$WorkingDirectory</workingdirectory>
  <startmode>Automatic</startmode>
  <onfailure action="restart" delay="10 sec" />
  <log mode="roll-by-size"><sizeThreshold>10240</sizeThreshold><keepFiles>8</keepFiles></log>
</service>
"@
    Set-Content -LiteralPath (Join-Path $serviceRoot "$Id.xml") -Value $xml -Encoding UTF8
    & $wrapper stop 2>$null | Out-Null
    & $wrapper uninstall 2>$null | Out-Null
    & $wrapper install | Out-Null
    & $wrapper start | Out-Null
}

Assert-Administrator
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "winget/App Installer diperlukan untuk instalasi online."
}
if (-not $PostgresSuperPassword) {
    throw "Isi -PostgresSuperPassword dengan password akun postgres lokal."
}
if ($PostgresSuperPassword -notmatch '^[A-Za-z0-9_-]{16,80}$') {
    throw "PostgresSuperPassword harus 16-80 karakter dan hanya memakai huruf, angka, _ atau -."
}
if (-not $DatabasePassword) { $DatabasePassword = New-RandomSecret 24 }
if (-not $AdminPassword) { $AdminPassword = New-RandomSecret 12 }
if ($DatabasePassword -notmatch '^[A-Za-z0-9_-]{16,80}$') {
    throw "DatabasePassword harus 16-80 karakter dan hanya memakai huruf, angka, _ atau -."
}
if ($SnmpCommunity -notmatch '^[A-Za-z0-9._-]{1,80}$') {
    throw "SnmpCommunity hanya boleh memakai huruf, angka, titik, _ atau -."
}

Install-WingetPackage "Python.Python.3.13"
Install-WingetPackage "OpenJS.NodeJS.LTS"
$postgresInstalled = winget list --id "PostgreSQL.PostgreSQL.17" --exact --accept-source-agreements 2>$null
if ($LASTEXITCODE -ne 0 -or ($postgresInstalled -join "`n") -notmatch "PostgreSQL.PostgreSQL.17") {
    $postgresOverride = "--mode unattended --superpassword $PostgresSuperPassword --servicename postgresql-x64-17 --serverport 5432"
    winget install --id "PostgreSQL.PostgreSQL.17" --exact --silent --accept-package-agreements --accept-source-agreements --disable-interactivity --override $postgresOverride
    if ($LASTEXITCODE -ne 0) { throw "Gagal memasang PostgreSQL 17." }
}
Install-WingetPackage "GrafanaLabs.Grafana"
Install-WingetPackage "CaddyServer.Caddy"
Install-WingetPackage "WinSW.WinSW"

$python = Find-Executable "python.exe" @("$env:LocalAppData\Programs\Python", "C:\Program Files\Python313")
$npm = Find-Executable "npm.cmd" @("C:\Program Files\nodejs")
$node = Find-Executable "node.exe" @("C:\Program Files\nodejs")
$psql = Find-Executable "psql.exe" @("C:\Program Files\PostgreSQL\17\bin")
$grafana = Find-Executable "grafana-server.exe" @("C:\Program Files\GrafanaLabs\grafana\bin")
$caddy = Find-Executable "caddy.exe" @("C:\Program Files", "$env:LocalAppData\Microsoft\WinGet\Packages")
$winsw = Find-Executable "WinSW*.exe" @("C:\Program Files", "$env:LocalAppData\Microsoft\WinGet\Packages")

New-Item -ItemType Directory -Path $InstallRoot, $DataRoot, "$DataRoot\config\file_sd", "$DataRoot\logs" -Force | Out-Null
robocopy "$repoRoot\backend" "$InstallRoot\backend" /E /XD .venv __pycache__ .pytest_cache "pytest-cache-files-*" | Out-Null
if ($LASTEXITCODE -ge 8) { throw "Gagal menyalin backend." }

$venv = Join-Path $DataRoot "venv"
if (-not (Test-Path "$venv\Scripts\python.exe")) { & $python -m venv $venv }
& "$venv\Scripts\python.exe" -m pip install --upgrade pip
& "$venv\Scripts\python.exe" -m pip install -r "$InstallRoot\backend\requirements.txt"

Push-Location "$repoRoot\frontend"
try {
    & $npm ci
    & $npm run build
} finally { Pop-Location }
New-Item -ItemType Directory -Path "$InstallRoot\frontend" -Force | Out-Null
robocopy "$repoRoot\frontend\.next\standalone" "$InstallRoot\frontend" /E | Out-Null
if ($LASTEXITCODE -ge 8) { throw "Gagal menyalin frontend standalone." }
robocopy "$repoRoot\frontend\.next\static" "$InstallRoot\frontend\.next\static" /E | Out-Null
robocopy "$repoRoot\frontend\public" "$InstallRoot\frontend\public" /E | Out-Null

$env:PGPASSWORD = $PostgresSuperPassword
$roleExists = & $psql -h 127.0.0.1 -U postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='monitoring'"
if (-not $roleExists) { & $psql -h 127.0.0.1 -U postgres -c "CREATE ROLE monitoring LOGIN PASSWORD '$DatabasePassword'" }
else { & $psql -h 127.0.0.1 -U postgres -c "ALTER ROLE monitoring PASSWORD '$DatabasePassword'" }
$dbExists = & $psql -h 127.0.0.1 -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='monitoring'"
if (-not $dbExists) { & $psql -h 127.0.0.1 -U postgres -c "CREATE DATABASE monitoring OWNER monitoring" }
Remove-Item Env:PGPASSWORD

$appSecret = New-RandomSecret
$credentialSecret = New-RandomSecret
$envFile = @"
APP_NAME=Pantau Infrastruktur
APP_ENV=production
DEPLOYMENT_PROFILE=windows_native
ENABLE_LIBRENMS=false
ENABLE_VMWARE=false
ENABLE_ADVANCED_TOPOLOGY=false
APP_SECRET_KEY=$appSecret
CREDENTIAL_ENCRYPTION_KEY=$credentialSecret
COOKIE_SECURE=false
ALLOWED_HOSTS=*
ADMIN_USERNAME=$AdminUsername
ADMIN_PASSWORD=$AdminPassword
DATABASE_URL=postgresql+psycopg://monitoring:$DatabasePassword@127.0.0.1:5432/monitoring
PROMETHEUS_URL=http://127.0.0.1:9090
BLACKBOX_EXPORTER_URL=http://127.0.0.1:9115
LIBRENMS_URL=http://127.0.0.1:8001
"@
Set-Content -LiteralPath "$InstallRoot\backend\.env" -Value $envFile -Encoding UTF8

Copy-Item "$repoRoot\infra\windows\prometheus.yml" "$DataRoot\config\prometheus.yml" -Force
Copy-Item "$repoRoot\infra\prometheus\rules.yml" "$DataRoot\config\rules.yml" -Force
Copy-Item "$repoRoot\infra\blackbox\blackbox.yml" "$DataRoot\config\blackbox.yml" -Force
Copy-Item "$repoRoot\infra\alertmanager\alertmanager.yml" "$DataRoot\config\alertmanager.yml" -Force
Copy-Item "$repoRoot\infra\snmp\auth.yml" "$DataRoot\config\snmp-auth.yml" -Force
(Get-Content "$DataRoot\config\snmp-auth.yml") -replace '\$\{SNMP_COMMUNITY\}',$SnmpCommunity | Set-Content "$DataRoot\config\snmp-auth.yml"
Copy-Item "$repoRoot\infra\windows\Caddyfile" "$DataRoot\config\Caddyfile" -Force
(Get-Content "$DataRoot\config\Caddyfile") -replace '^:8080',":$HttpPort" | Set-Content "$DataRoot\config\Caddyfile"

$prometheusRoot = Install-PrometheusArchive "prometheus" "3.11.3" "prometheus-3.11.3.windows-amd64.zip"
$alertmanagerRoot = Install-PrometheusArchive "alertmanager" "0.32.1" "alertmanager-0.32.1.windows-amd64.zip"
$blackboxRoot = Install-PrometheusArchive "blackbox_exporter" "0.28.0" "blackbox_exporter-0.28.0.windows-amd64.zip"
$snmpRoot = Install-PrometheusArchive "snmp_exporter" "0.30.1" "snmp_exporter-0.30.1.windows-amd64.zip"

Push-Location "$InstallRoot\backend"
try {
    & "$venv\Scripts\python.exe" -m alembic upgrade head
    & "$venv\Scripts\python.exe" -m app.bootstrap
} finally { Pop-Location }

Install-WrappedService "MonitoraBackend" "Monitora Backend" "$venv\Scripts\python.exe" "-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers" "$InstallRoot\backend" $winsw
Install-WrappedService "MonitoraFrontend" "Monitora Frontend" $node "server.js" "$InstallRoot\frontend" $winsw
Install-WrappedService "MonitoraPrometheus" "Monitora Prometheus" "$prometheusRoot\prometheus.exe" "--config.file=$DataRoot\config\prometheus.yml --storage.tsdb.path=$DataRoot\prometheus --storage.tsdb.retention.time=30d --storage.tsdb.retention.size=8GB --web.enable-lifecycle" $prometheusRoot $winsw
Install-WrappedService "MonitoraAlertmanager" "Monitora Alertmanager" "$alertmanagerRoot\alertmanager.exe" "--config.file=$DataRoot\config\alertmanager.yml --storage.path=$DataRoot\alertmanager" $alertmanagerRoot $winsw
Install-WrappedService "MonitoraBlackbox" "Monitora Blackbox Exporter" "$blackboxRoot\blackbox_exporter.exe" "--config.file=$DataRoot\config\blackbox.yml" $blackboxRoot $winsw
Install-WrappedService "MonitoraSnmp" "Monitora SNMP Exporter" "$snmpRoot\snmp_exporter.exe" "--config.file=$snmpRoot\snmp.yml --config.file=$DataRoot\config\snmp-auth.yml" $snmpRoot $winsw

$grafanaRoot = Split-Path -Parent (Split-Path -Parent $grafana)
$grafanaProvisioning = "$DataRoot\grafana\provisioning"
New-Item -ItemType Directory -Path "$grafanaProvisioning\datasources", "$grafanaProvisioning\dashboards", "$DataRoot\grafana\dashboards", "$DataRoot\grafana\data" -Force | Out-Null
Copy-Item "$repoRoot\infra\grafana\provisioning\datasources\prometheus.yml" "$grafanaProvisioning\datasources\prometheus.yml" -Force
(Get-Content "$grafanaProvisioning\datasources\prometheus.yml") -replace 'http://prometheus:9090','http://127.0.0.1:9090' | Set-Content "$grafanaProvisioning\datasources\prometheus.yml"
Copy-Item "$repoRoot\infra\grafana\provisioning\dashboards\default.yml" "$grafanaProvisioning\dashboards\default.yml" -Force
(Get-Content "$grafanaProvisioning\dashboards\default.yml") -replace '/var/lib/grafana/dashboards',($DataRoot -replace '\\','/') + '/grafana/dashboards' | Set-Content "$grafanaProvisioning\dashboards\default.yml"
Copy-Item "$repoRoot\infra\grafana\dashboards\*" "$DataRoot\grafana\dashboards" -Force
[Environment]::SetEnvironmentVariable("GF_PATHS_DATA", "$DataRoot\grafana\data", "Machine")
[Environment]::SetEnvironmentVariable("GF_PATHS_PROVISIONING", $grafanaProvisioning, "Machine")
[Environment]::SetEnvironmentVariable("GF_SERVER_HTTP_PORT", "3001", "Machine")
[Environment]::SetEnvironmentVariable("GF_SERVER_ROOT_URL", "http://localhost:$HttpPort/grafana/", "Machine")
[Environment]::SetEnvironmentVariable("GF_SERVER_SERVE_FROM_SUB_PATH", "true", "Machine")
[Environment]::SetEnvironmentVariable("GF_AUTH_ANONYMOUS_ENABLED", "true", "Machine")
[Environment]::SetEnvironmentVariable("GF_AUTH_ANONYMOUS_ORG_ROLE", "Viewer", "Machine")
Restart-Service grafana -ErrorAction SilentlyContinue

& sc.exe stop MonitoraGateway 2>$null | Out-Null
& sc.exe delete MonitoraGateway 2>$null | Out-Null
& sc.exe create MonitoraGateway start= auto binPath= "`"$caddy`" run --config `"$DataRoot\config\Caddyfile`"" | Out-Null
& sc.exe start MonitoraGateway | Out-Null

& "$PSScriptRoot\install-windows-agent.ps1" -MonitoringServer "127.0.0.1"
Get-NetFirewallRule -DisplayName "Monitora Portal" -ErrorAction SilentlyContinue | Remove-NetFirewallRule
New-NetFirewallRule -DisplayName "Monitora Portal" -Direction Inbound -Action Allow -Protocol TCP -LocalPort $HttpPort -RemoteAddress LocalSubnet | Out-Null

Write-Host "Monitora selesai dipasang pada http://localhost:$HttpPort"
Write-Host "Username awal: $AdminUsername"
Write-Host "Password awal: $AdminPassword"
Write-Host "Simpan password ini lalu ganti setelah login pertama."
