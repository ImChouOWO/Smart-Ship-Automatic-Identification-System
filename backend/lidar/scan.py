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

# ✅ 最大顯示距離（單位：mm），可依需求調整
MAX_DISTANCE = 1000  # 例如設為 20 公尺 = 20000 mm

def initialize_uart():
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT)
        if ser.is_open:
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
            angle = (angle_q2 / 64.0) * (np.pi / 180.0)
            distance = distance_q2 / 4.0
            if distance <= MAX_DISTANCE:  # ✅ 僅保留指定距離內的點
                results.append((angle, distance))
    return results

# 初始化圖表（黑色背景 + 紅點）
fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
sc = ax.scatter([], [], c='red', s=3, alpha=0.8)
ax.set_theta_zero_location('N')
ax.set_theta_direction(-1)
ax.set_ylim(0, MAX_DISTANCE)  # ✅ 動態設定最大距離

# 多圈歷史資料儲存
scan_history = []
history_limit = 10
last_angle = None

def update(frame):
    global last_angle, scan_history

    data = ser.read(1024)
    results = parse_scan_data(data)

    if results:
        angles, distances = zip(*results)
        angles = np.array(angles)
        distances = np.array(distances)

        if last_angle is not None and np.any(angles < last_angle - np.pi):
            scan_history.append(results)
            if len(scan_history) > history_limit:
                scan_history.pop(0)

        last_angle = np.max(angles)

        if not scan_history or (scan_history and scan_history[-1] is not results):
            if scan_history:
                scan_history[-1].extend(results)
            else:
                scan_history.append(results)

        merged = [pt for circle in scan_history for pt in circle]
        if merged:
            angles, distances = zip(*merged)
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
