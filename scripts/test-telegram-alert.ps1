<#
.SYNOPSIS
    Skrip untuk menguji notifikasi Telegram pada Monitora.
.DESCRIPTION
    Skrip ini memiliki 2 mode pengujian:
    1. Direct API Test: Menguji token bot dan chat ID langsung ke Telegram Bot API.
    2. Alertmanager Test: Mengirimkan alert tiruan (mock firing alert) ke Alertmanager lokal.
.EXAMPLE
    .\scripts\test-telegram-alert.ps1 -DirectTest
.EXAMPLE
    .\scripts\test-telegram-alert.ps1 -AlertmanagerTest
#>

param(
    [switch]$DirectTest = $false,
    [switch]$AlertmanagerTest = $false,
    [string]$BotToken = "",
    [string]$ChatId = ""
)

$secretsFile = Join-Path $PSScriptRoot "..\secrets\telegram_bot_token"
$configYaml = Join-Path $PSScriptRoot "..\infra\alertmanager\telegram.yml"

# Ambil token jika tidak diisi via param
if (-not $BotToken) {
    if (Test-Path $secretsFile) {
        $BotToken = (Get-Content $secretsFile -Raw).Trim()
    }
}

# Ambil chat ID dari telegram.yml jika tidak diisi via param
if (-not $ChatId) {
    if (Test-Path $configYaml) {
        $content = Get-Content $configYaml -Raw
        if ($content -match 'chat_id:\s*([^\r\n#]+)') {
            $ChatId = $matches[1].Trim()
        }
    }
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   MONITORA - PENGUJIAN ALERT TELEGRAM    " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

if (-not $BotToken -or $BotToken -eq "1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ1234567") {
    Write-Host "[!] Bot Token belum diset dengan benar." -ForegroundColor Yellow
    Write-Host "    Silakan isi token dari @BotFather ke file: secrets/telegram_bot_token" -ForegroundColor Yellow
    exit 1
}

if (-not $ChatId -or $ChatId -eq "000000000") {
    Write-Host "[!] Chat ID belum diset dengan benar." -ForegroundColor Yellow
    Write-Host "    Silakan ubah 'chat_id' pada file: infra/alertmanager/telegram.yml" -ForegroundColor Yellow
    exit 1
}

# Default jalankan DirectTest jika tidak ada switch
if (-not $DirectTest -and -not $AlertmanagerTest) {
    $DirectTest = $true
}

if ($DirectTest) {
    Write-Host "`n[*] Menguji koneksi langsung ke Telegram API..." -ForegroundColor Green
    $uri = "https://api.telegram.org/bot$BotToken/sendMessage"
    $testMessage = @"
🔥 <b>ALARM INFRASTRUKTUR (PENGUJIAN)</b>

<b>Alert:</b> UjiCobaNotifikasi
<b>Tingkat:</b> ⚠️ WARNING
<b>Target:</b> <code>Monitora-Local</code>
<b>Perangkat:</b> Server Monitoring

<b>Rincian:</b>
• Konfigurasi bot Telegram Monitora berhasil terhubung!
  <i>Ini adalah pesan verifikasi sistem alerting.</i>
"@

    $body = @{
        chat_id    = $ChatId
        text       = $testMessage
        parse_mode = "HTML"
    } | ConvertTo-Json

    try {
        $response = Invoke-RestMethod -Uri $uri -Method Post -Body $body -ContentType "application/json"
        if ($response.ok) {
            Write-Host "[✓] Berhasil mengirim pesan uji coba ke Telegram!" -ForegroundColor Green
            Write-Host "    Pesan terkirim ke chat ID: $ChatId" -ForegroundColor Cyan
        } else {
            Write-Host "[X] Telegram merespons tetapi status gagal: $($response | ConvertTo-Json)" -ForegroundColor Red
        }
    } catch {
        Write-Host "[X] Gagal menghubungi Telegram API: $_" -ForegroundColor Red
    }
}

if ($AlertmanagerTest) {
    Write-Host "`n[*] Mengirim alert simulasi ke Alertmanager (http://localhost:9093)..." -ForegroundColor Green
    $alertmanagerUri = "http://localhost:9093/api/v1/alerts"
    
    $now = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
    $mockAlert = @(
        @{
            labels = @{
                alertname = "PenggunaanMemoriKritis"
                instance  = "server-test:9100"
                severity  = "critical"
            }
            annotations = @{
                summary     = "Memori server-test:9100 kritis di atas 95%"
                description = "Uji coba alert resource kritis dari skrip pengujian."
            }
            startsAt = $now
        }
    ) | ConvertTo-Json -Depth 4

    try {
        $res = Invoke-RestMethod -Uri $alertmanagerUri -Method Post -Body $mockAlert -ContentType "application/json"
        Write-Host "[✓] Alert simulasi berhasil dikirim ke Alertmanager!" -ForegroundColor Green
        Write-Host "    Alertmanager akan merender template dan meneruskan pesan ke Telegram dalam beberapa detik." -ForegroundColor Cyan
    } catch {
        Write-Host "[!] Tidak dapat menghubungi Alertmanager di localhost:9093." -ForegroundColor Yellow
        Write-Host "    Pastikan Alertmanager sudah berjalan dengan container Docker:" -ForegroundColor Gray
        Write-Host "    docker compose -f compose.yaml -f compose.telegram.yaml up -d alertmanager" -ForegroundColor Gray
    }
}

Write-Host "`nSelesai." -ForegroundColor Cyan
