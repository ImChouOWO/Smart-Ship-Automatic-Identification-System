import serial
import struct
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time

# UART 設定
PORT = '/dev/ttyUSB5'
BAUDRATE = 1000000
TIMEOUT = 1

START_SCAN = b'\xA5\x20'
STOP_SCAN = b'\xA5\x25'

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
            # 可取消品質過濾條件以顯示更多點
            results.append((angle, distance, quality))
    return results

# 畫圖初始化
fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
sc = ax.scatter([], [], c=[], cmap='viridis', s=10, edgecolors='k', alpha=0.75)
cbar = plt.colorbar(sc, ax=ax, orientation='vertical', label='Quality')  # 確保有 colorbar
ax.set_theta_zero_location('N')
ax.set_theta_direction(-1)
ax.set_ylim(0, 30000)  # S2E 最大距離 30 公尺

# 資料儲存
scan_history = []     # 儲存每一圈掃描的資料
history_limit = 10    # 最多保留 10 圈
last_angle = None

def update(frame):
    global last_angle, scan_history

    data = ser.read(1024)
    results = parse_scan_data(data)

    if results:
        angles, distances, qualities = zip(*results)
        angles = np.array(angles)
        distances = np.array(distances)

        # 檢測是否進入新的一圈
        if last_angle is not None and np.any(angles < last_angle - np.pi):
            # 新一圈開始：新增並裁剪歷史資料
            scan_history.append(results)
            if len(scan_history) > history_limit:
                scan_history.pop(0)  # 移除最舊那圈

        last_angle = np.max(angles)

        # 若沒進入新圈，直接補在最後一圈中
        if not scan_history or (scan_history and scan_history[-1] is not results):
            if scan_history:
                scan_history[-1].extend(results)
            else:
                scan_history.append(results)

        # 合併所有掃描圈以便繪圖
        merged = [pt for scan in scan_history for pt in scan]
        if merged:
            angles, distances, qualities = zip(*merged)
            x = np.array(distances) * np.cos(angles)
            y = np.array(distances) * np.sin(angles)
            sc.set_offsets(np.c_[x, y])
            sc.set_array(np.array(qualities))  # 更新 colorbar 映射

    return sc,

# 主程式
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
