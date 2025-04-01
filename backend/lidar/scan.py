import serial
import struct
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# 黑底風格
plt.style.use('dark_background')

# UART 設定
PORT = '/dev/ttyUSB5'
BAUDRATE = 1000000
TIMEOUT = 1

START_SCAN = b'\xA5\x20'
STOP_SCAN = b'\xA5\x25'

# 顯示範圍參數
MAX_DISTANCE = 4000      # 最遠距離（mm）
MAX_HISTORY = 60         # 最多保留幾圈

def initialize_uart():
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT)
        print(f"✅ Serial port {PORT} opened successfully.")
        return ser
    except Exception as e:
        print(f"❌ Failed to open serial port: {e}")
        exit(1)

def start_scan(ser):
    print("🔄 Starting scan...")
    ser.write(START_SCAN)

def stop_scan(ser):
    print("🛑 Stopping scan...")
    ser.write(STOP_SCAN)

def parse_scan_data(data):
    results = []
    if len(data) < 7:
        return results

    for i in range(0, len(data) - 6, 7):
        if data[i] & 0x01 == 0x01 and data[i + 1] & 0x01 == 0x01:
            angle_q2, distance_q2, quality = struct.unpack('<HHB', data[i + 2:i + 7])
            angle_deg = angle_q2 / 64.0
            angle_rad = np.radians(angle_deg)
            distance = distance_q2 / 4.0  # 距離單位為 mm
            if distance <= MAX_DISTANCE:
                results.append((angle_rad, distance))
    return results

# 畫圖初始化：笛卡兒坐標
fig, ax = plt.subplots()
sc = ax.scatter([], [], c='cyan', s=2, alpha=0.6)
ax.set_xlim(-MAX_DISTANCE, MAX_DISTANCE)
ax.set_ylim(-MAX_DISTANCE, MAX_DISTANCE)
ax.set_aspect('equal')
ax.set_title('RPLidar 2D Mapping')
ax.set_xlabel('X [mm]')
ax.set_ylabel('Y [mm]')

# 資料記錄
scan_history = []

def update(frame):
    data = ser.read(1024)
    results = parse_scan_data(data)

    if results:
        scan_history.append(results)
        if len(scan_history) > MAX_HISTORY:
            scan_history.pop(0)

        all_points = [pt for scan in scan_history for pt in scan]
        angles, distances = zip(*all_points)
        x = np.array(distances) * np.cos(angles)
        y = np.array(distances) * np.sin(angles)
        sc.set_offsets(np.c_[x, y])

    return sc,

def main():
    global ser
    ser = initialize_uart()
    start_scan(ser)

    ani = FuncAnimation(fig, update, interval=100, blit=False)
    plt.show()

    stop_scan(ser)
    ser.close()
    print("🔒 Serial port closed.")

if __name__ == "__main__":
    main()
