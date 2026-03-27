# 1. รัน ngrok (ตรวจสอบว่ามี ngrok.exe อยู่ใน PATH หรือโฟลเดอร์นี้)
Write-Host "--- Starting ngrok ---" -ForegroundColor Cyan
# รัน ngrok แบบแยกหน้าต่างออกมาเพื่อให้เห็น Log (หรือใส่ -WindowStyle Hidden ถ้าต้องการซ่อน)
Start-Process "C:\ngrok-v3-stable-windows-amd64\ngrok.exe" -ArgumentList "start --all --config ./ngrok.yml"

# รอ ngrok เชื่อมต่อ 7 วินาทีเพื่อให้มั่นใจว่า Tunnel มาครบ
Write-Host "Waiting for ngrok to initialize..."
Start-Sleep -Seconds 7

# 2. ดึงค่าจาก ngrok API ด้วย PowerShell ล้วนๆ (ไม่ต้องใช้ jq)
try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels"
    $tcp_tunnel = $response.tunnels | Where-Object { $_.proto -eq "tcp" }

    if ($null -eq $tcp_tunnel) {
        Write-Host "Error: TCP Tunnel not found! Make sure ngrok.yml has a TCP tunnel configured." -ForegroundColor Red
        exit
    }

    # 3. แยก Host และ Port (ตัด tcp:// ออก)
    # เช่นจาก tcp://0.tcp.ap.ngrok.io:12345 -> 0.tcp.ap.ngrok.io และ 12345
    $address = $tcp_tunnel.public_url.Replace("tcp://", "")
    $mqtt_host_ext = $address.Split(":")[0]
    $mqtt_port_ext = $address.Split(":")[1]

    Write-Host "`n======================================" -ForegroundColor Green
    Write-Host " MQTT EXTERNAL CONFIG READY " -ForegroundColor Green
    Write-Host " Host: $mqtt_host_ext"
    Write-Host " Port: $mqtt_port_ext"
    Write-Host "======================================" -ForegroundColor Green

    # 4. ตั้งค่า Environment Variable สำหรับ Session นี้
    $env:MQTT_HOST_EXTERNAL = $mqtt_host_ext
    $env:MQTT_PORT_EXTERNAL = $mqtt_port_ext

    # 5. สั่ง Docker Compose Up
    Write-Host "Starting Docker Containers..." -ForegroundColor Yellow
    docker-compose build --no-cache api
    docker-compose up -d --remove-orphans
    
    Write-Host "`nSystem is UP! API is now using the latest ngrok port." -ForegroundColor Cyan
}
catch {
    Write-Host "Error: Could not connect to ngrok API. Is ngrok running?" -ForegroundColor Red
}