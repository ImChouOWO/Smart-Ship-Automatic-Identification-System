import serial
import struct
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# UART 設定
PORT = '/dev/ttyUSB0'
BAUDRATE = 1000000
TIMEOUT = 1

# RPLIDAR 指令
START_SCAN = b'\xA5\x20'
STOP_SCAN = b'\xA5\x25'

# 初始化 UART 串口
def initialize_uart():
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT)
        if ser.is_open:
            print(f"✅ Serial port {PORT} opened successfully.")
        return ser
    except Exception as e:
        print(f"❌ Failed to open serial port: {e}")
        exit(1)

# 啟動掃描
def start_scan(ser):
    print("🔄 Starting scan...")
    ser.write(START_SCAN)

# 停止掃描
def stop_scan(ser):
    print("🛑 Stopping scan...")
    ser.write(STOP_SCAN)

# 解析掃描數據
def parse_scan_data(data):
    results = []
    if len(data) < 7:
        return results

    for i in range(0, len(data) - 6, 7):
        if data[i] & 0x01 == 0x01 and data[i + 1] & 0x01 == 0x01:
            angle_q2, distance_q2, quality = struct.unpack('<HHB', data[i + 2:i + 7])
            angle = (angle_q2 / 64.0) * (np.pi / 180.0)
            distance = distance_q2 / 4.0
            MIN_QUALITY = 30
            if quality >= MIN_QUALITY:
                results.append((angle, distance, quality))
    return results

# 畫圖初始化
fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
sc = ax.scatter([], [], c=[], cmap='viridis', s=10, edgecolors='k', alpha=0.75)
ax.set_theta_zero_location('N')
ax.set_theta_direction(-1)
cbar = plt.colorbar(sc, ax=ax, orientation='vertical', label='Quality')
ax.set_ylim(0, 30000)  # 根據 S2E 最大距離：30m = 30000mm

# 存儲目前掃描圈的數據
current_scan = []
last_angle = None

def update(frame):
    global last_angle, current_scan

    data = ser.read(1024)  # 每幀讀取更多資料
    results = parse_scan_data(data)

    if results:
        angles, distances, qualities = zip(*results)
        angles = np.array(angles)
        distances = np.array(distances)

        if last_angle is not None and np.any(angles < last_angle - np.pi):
            current_scan.clear()

        last_angle = np.max(angles)
        current_scan = list(zip(angles, distances, qualities))

        if current_scan:
            angles, distances, qualities = zip(*current_scan)
            x = distances * np.cos(angles)
            y = distances * np.sin(angles)

            sc.set_offsets(np.c_[x, y])
            sc.set_array(np.array(qualities))

    return sc,

# 主程式
def main():
    global ser
    ser = initialize_uart()
    start_scan(ser)

    # ✅ 調整 interval = 100 毫秒 (10Hz)
    ani = FuncAnimation(fig, update, interval=100, blit=False)

    plt.show()
    stop_scan(ser)
    ser.close()
    print("🔒 Serial port closed.")

if __name__ == "__main__":
    main()
