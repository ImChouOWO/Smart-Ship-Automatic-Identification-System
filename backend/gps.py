import os
import fcntl
import subprocess
import serial
import time
import math

USBDEVFS_RESET = 21780

def reset_usb(dev_bus_device_path):
    try:
        with open(dev_bus_device_path, 'rb') as f:
            fcntl.ioctl(f, USBDEVFS_RESET, 0)
        print(f"🔄 成功重啟 USB 裝置: {dev_bus_device_path}")
        return True
    except Exception as e:
        print(f"❌ 無法重啟 USB 裝置 {dev_bus_device_path}: {e}")
        return False

def get_usb_bus_device_path(dev_node="/dev/ttyACM0"):
    try:
        output = subprocess.check_output(
            f"udevadm info -q path -n {dev_node}", shell=True
        ).decode().strip()
        usb_path = f"/sys{output}"
        for root, dirs, files in os.walk(usb_path):
            if "busnum" in files and "devnum" in files:
                with open(os.path.join(root, "busnum")) as f:
                    bus = int(f.read().strip())
                with open(os.path.join(root, "devnum")) as f:
                    dev = int(f.read().strip())
                return f"/dev/bus/usb/{bus:03d}/{dev:03d}"
    except Exception as e:
        print(f"❌ 查找 USB 裝置路徑失敗: {e}")
    return None

def reset_gps_usb(dev_node="/dev/ttyACM0"):
    path = get_usb_bus_device_path(dev_node)
    if path:
        return reset_usb(path)
    else:
        print("⚠️ 無法找到 USB 裝置對應路徑")
        return False

def parse_nmea_gpgga(sentence):
    if sentence.startswith('$GPGGA'):
        parts = sentence.split(',')
        if len(parts) >= 10 and parts[6] != '0':
            time_str = parts[1]
            lat_raw, lat_dir = parts[2], parts[3]
            lon_raw, lon_dir = parts[4], parts[5]
            alt = parts[9]

            # 緯度轉換
            lat_deg = float(lat_raw[:2]) + float(lat_raw[2:]) / 60 if lat_raw else 0
            if lat_dir == 'S':
                lat_deg = -lat_deg
            lon_deg = float(lon_raw[:3]) + float(lon_raw[3:]) / 60 if lon_raw else 0
            if lon_dir == 'W':
                lon_deg = -lon_deg

            return time_str, lat_deg, lon_deg, float(alt)
    return None, None, None, None

def calculate_bearing(lat1, lon1, lat2, lon2):
    """
    計算從第一個點到第二個點的方位角（以北為 0 度，順時針）
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    x = math.sin(delta_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - \
        math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    bearing = math.atan2(x, y)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    return bearing

# GPS 初始化
port = "/dev/gps"
baud = 4800
invalid_nmea_count = 0
MAX_INVALID_COUNT = 10

# 緯經度紀錄
last_lat, last_lon = None, None

try:
    ser = serial.Serial(port, baudrate=baud, timeout=2)
except Exception as e:
    print(f"❌ 無法打開串口 {port}: {e}")
    exit(1)

while True:
    try:
        line = ser.readline().decode('ascii', errors='replace').strip()
        if line.startswith('$GPGGA'):
            time_str, lat, lon, alt = parse_nmea_gpgga(line)
            if time_str and lat and lon:
                print(f"🕒 時間: {time_str}")
                print(f"🧭 緯度: {lat:.6f}°")
                print(f"🧭 經度: {lon:.6f}°")
                print(f"🗻 海拔: {alt} M")

                if last_lat is not None and last_lon is not None:
                    heading = calculate_bearing(last_lat, last_lon, lat, lon)
                    print(f"➡️ 預估航向角（GPS Heading）: {heading:.2f}°")
                    break

                last_lat, last_lon = lat, lon  # 記錄第一個點
            else:
                invalid_nmea_count += 1
                print(f"⚠️ GPGGA 無效，第 {invalid_nmea_count} 次")

        if invalid_nmea_count >= MAX_INVALID_COUNT:
            print("🧯 重啟 GPS USB 裝置")
            ser.close()
            if not reset_gps_usb(port):
                print("❌ 重啟 USB 失敗，結束程式")
                break
            time.sleep(3)
            ser = serial.Serial(port, baudrate=baud, timeout=2)
            invalid_nmea_count = 0

    except KeyboardInterrupt:
        print("🛑 程式中斷")
        break
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        break

ser.close()
