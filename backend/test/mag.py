import serial
import time
import matplotlib.pyplot as plt

# 初始化序列埠
ser = serial.Serial('/dev/imu', 9600, timeout=0.5)

# 儲存磁力數據
mag_x_vals = []
mag_y_vals = []

# 抽取封包並解碼磁力資料（參照你原本的格式）
def parse_mag_packet(packet):
    if len(packet) != 11 or packet[1] != 0x54:
        return None
    mx = (packet[3] << 8 | packet[2]) / 32768.0
    my = (packet[5] << 8 | packet[4]) / 32768.0
    mz = (packet[7] << 8 | packet[6]) / 32768.0
    if mx >= 1.0: mx -= 2.0
    if my >= 1.0: my -= 2.0
    if mz >= 1.0: mz -= 2.0
    return mx, my, mz

print("📡 開始讀取磁力計資料，旋轉你的模組...")

try:
    while len(mag_x_vals) < 300:
        byte = ser.read()
        if not byte:
            continue
        if byte == b'\x55':
            pkt = ser.read(10)
            if len(pkt) == 10:
                full_packet = byte + pkt
                result = parse_mag_packet(list(full_packet))
                if result:
                    mx, my, mz = result
                    mag_x_vals.append(mx)
                    mag_y_vals.append(my)
                    print(f"🧲 MagX: {mx:.3f}, MagY: {my:.3f}, MagZ: {mz:.3f}")
except KeyboardInterrupt:
    pass
finally:
    ser.close()
    print("🔚 結束串口")

# 畫出磁力計 XY 平面分布圖
plt.figure(figsize=(6, 6))
plt.scatter(mag_x_vals, mag_y_vals, c='blue', s=10)
plt.title("Magnetometer X-Y Raw Output")
plt.xlabel("Mag X")
plt.ylabel("Mag Y")
plt.grid(True)
plt.axis("equal")
plt.show()
