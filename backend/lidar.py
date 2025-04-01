# lidar.py
import serial
import struct
import numpy as np
import time

PORT = '/dev/ttyUSB5'
BAUDRATE = 1000000
TIMEOUT = 1
START_SCAN = b'\xA5\x20'
STOP_SCAN = b'\xA5\x25'

def initialize_uart():
    ser = serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT)
    return ser

def parse_scan_data(data):
    results = []
    if len(data) < 7:
        return results

    for i in range(0, len(data) - 6, 7):
        if data[i] & 0x01 == 0x01 and data[i + 1] & 0x01 == 0x01:
            angle_q2, distance_q2, quality = struct.unpack('<HHB', data[i + 2:i + 7])
            angle = (angle_q2 / 64.0) * (np.pi / 180.0)
            distance = distance_q2 / 4.0
            if quality >= 30:
                results.append((angle, distance, quality))
    return results

def start_lidar_scan(callback=None):
    ser = initialize_uart()
    ser.write(START_SCAN)
    print("🔄 LIDAR scanning started...")

    last_angle = None
    current_scan = []

    try:
        while True:
            data = ser.read(1024)
            results = parse_scan_data(data)
            if results:
                angles = [r[0] for r in results]
                if last_angle is not None and any(a < last_angle - np.pi for a in angles):
                    # 新的一圈開始
                    if callback:
                        callback(current_scan)
                    current_scan = []
                last_angle = max(angles)
                current_scan.extend(results)
    except KeyboardInterrupt:
        pass
    finally:
        ser.write(STOP_SCAN)
        ser.close()
        print("🛑 LIDAR scan stopped.")
