import serial
import time

# === 設定 COM Port 與鮑率 ===
COM_PORT = "COM4"         # 請依照實際連接的 USB-to-TTL COM port 更改
BAUD_RATE = 9600
TIMEOUT = 0.5               # 秒數

# === 建立 serial 連線 ===
ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=TIMEOUT)
time.sleep(2)  # 等待 Arduino 重啟

# === 模擬封包：送出合法封包（GPS/IMU 格式）===
# 封包結構為 31 bytes，模擬資料來源：
# 緯度 23.567000 -> 0x03 0x90 0x88  (即：2356700)
# 經度 120.985000 -> 0x12 0x78 0xD4 (即：12098500)
# Yaw = 20.0 -> 20000 -> 0x4E 0x20

packet = bytearray([
    0x1B, 0x04, 0x01, 0x01, 0x0E,  # Header & meta
    0x03, 0x90, 0x88,              # Latitude
    0x7C,
    0x12, 0x78, 0xD4,              # Longitude
    0x7C, 0x00,                    # Separator
    0x7C,                          # Yaw separator
    0x00, 0x00,                    # Roll
    0x00, 0x00,                    # Pitch
    0x4E, 0x20,                    # Yaw = 20.000
    0x00, 0x00, 0x00, 0x00,        # Padding
    0x00, 0x00, 0x00,              # More padding
    0x00                           # Placeholder for BCC
])

# === 計算 BCC（XOR 最後一個 byte）===
def calculate_bcc(data):
    bcc = 0
    for b in data[:-1]:  # 最後一個是 bcc 本身
        bcc ^= b
    return bcc

packet[-1] = calculate_bcc(packet)

# === 傳送封包 ===
ser.write(packet)
print("[PC] 🚀 傳送封包完成，等待 Arduino 回應...")

# === 接收回應（應含「Sent navigation packet」等回饋）===
time.sleep(0.5)
while ser.in_waiting:
    response = ser.readline().decode(errors='ignore').strip()
    if response:
        print(f"[Arduino 回應] {response}")

ser.close()
