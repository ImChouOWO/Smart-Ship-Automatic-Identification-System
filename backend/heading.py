# coding: UTF-8
import serial
import threading
import time
import math

# === IMU 設定 ===
imu_port = '/dev/imu'
imu_baud = 9600
imu_heading = None

# === GPS 設定 ===
gps_port = '/dev/gps'
gps_baud = 4800
gps_heading = None
last_lat, last_lon = None, None

# === IMU 處理 ===
def to_signed(val):
    return val - 65536 if val > 32767 else val

def get_angle(datahex):
    roll = to_signed(datahex[1] << 8 | datahex[0]) / 32768.0 * 180.0
    pitch = to_signed(datahex[3] << 8 | datahex[2]) / 32768.0 * 180.0
    yaw = to_signed(datahex[5] << 8 | datahex[4]) / 32768.0 * 180.0
    return roll, pitch, yaw

def read_imu():
    global imu_heading
    buf_length = 11
    RxBuff = [0] * buf_length
    CheckSum = 0
    start = 0
    data_length = 0
    ser = serial.Serial(imu_port, imu_baud, timeout=0.5)

    while True:
        data = ser.read(1)
        if not data:
            continue
        byte = int(data.hex(), 16)

        if byte == 0x55 and start == 0:
            start = 1
            data_length = 11
            CheckSum = 0
            RxBuff = [0] * buf_length

        if start == 1:
            CheckSum += byte
            RxBuff[buf_length - data_length] = byte
            data_length -= 1
            if data_length == 0:
                CheckSum = (CheckSum - byte) & 0xFF
                start = 0
                if RxBuff[buf_length - 1] != CheckSum:
                    continue
                if RxBuff[1] == 0x53:
                    angle = get_angle(RxBuff[2:8])
                    yaw = (angle[2] + 360) % 360
                    imu_heading = yaw

# === GPS 處理 ===
def parse_nmea_gpgga(sentence):
    if sentence.startswith('$GPGGA'):
        parts = sentence.split(',')
        if len(parts) >= 10 and parts[6] != '0':
            lat_raw, lat_dir = parts[2], parts[3]
            lon_raw, lon_dir = parts[4], parts[5]

            lat_deg = float(lat_raw[:2]) + float(lat_raw[2:]) / 60 if lat_raw else 0
            if lat_dir == 'S':
                lat_deg = -lat_deg
            lon_deg = float(lon_raw[:3]) + float(lon_raw[3:]) / 60 if lon_raw else 0
            if lon_dir == 'W':
                lon_deg = -lon_deg

            return lat_deg, lon_deg
    return None, None

def calculate_bearing(lat1, lon1, lat2, lon2):
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)
    x = math.sin(delta_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing = math.atan2(x, y)
    return (math.degrees(bearing) + 360) % 360

def read_gps():
    global gps_heading, last_lat, last_lon
    ser = serial.Serial(gps_port, gps_baud, timeout=2)
    while True:
        try:
            line = ser.readline().decode('ascii', errors='replace').strip()
            if line.startswith('$GPGGA'):
                lat, lon = parse_nmea_gpgga(line)
                if lat and lon:
                    if last_lat and last_lon:
                        gps_heading = calculate_bearing(last_lat, last_lon, lat, lon)
                    last_lat, last_lon = lat, lon
        except:
            continue

# === 啟動執行緒 ===
threading.Thread(target=read_imu, daemon=True).start()
threading.Thread(target=read_gps, daemon=True).start()

# === 主迴圈每秒顯示一次 ===
while True:
    print("==== Heading 資訊 ====")
    if imu_heading is not None:
        print(f"📡 IMU Heading : {imu_heading:.2f}°")
    if gps_heading is not None:
        print(f"🛰️ GPS Heading : {gps_heading:.2f}°")
    print()
    time.sleep(1)
