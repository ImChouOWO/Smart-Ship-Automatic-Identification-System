# device_a_client.py
import socketio
import time
import random

# 固定 IP server 的 IP，請替換成你的裝置 B IP
SERVER_URL = 'http://192.168.1.100:5000'  # 或公開 IP

sio = socketio.Client()

@sio.event
def connect():
    print("✅ Connected to server")

@sio.event
def disconnect():
    print("❌ Disconnected from server")

sio.connect(SERVER_URL)

# 模擬定期上報資料
try:
    while True:
        data = {
            "temperature": round(random.uniform(25.0, 30.0), 2),
            "humidity": round(random.uniform(60.0, 70.0), 2),
        }
        sio.emit("device_data", data)
        print("📤 Sent:", data)
        time.sleep(5)  # 每 5 秒發一次
except KeyboardInterrupt:
    sio.disconnect()
