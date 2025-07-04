# coding:UTF-8
# Version: V2.0 - Gyro-based Yaw with reset every 10s

import serial
import math
import time

buf_length = 11
RxBuff = [0]*buf_length

GYROData = [0.0]*8

# 全域變數
yaw = 0.0
last_time = None
last_reset = time.time()

# 側轉閾值、reset 週期
GYRO_THRESHOLD = 1.0   # deg/s 以下視為靜止
RESET_INTERVAL = 10.0  # 每 10 秒重設 yaw

def get_gyro(datahex):
    wxl, wxh, wyl, wyh, wzl, wzh = datahex[:6]
    k = 2000.0
    gz = (wzh << 8 | wzl) / 32768.0 * k
    if gz >= k: gz -= 2 * k
    return gz

def GetDataDeal(buf):
    global gz_latest
    if buf[-1] != CheckSum: return False
    if buf[1] == 0x52:
        for i in range(6):
            GYROData[i] = buf[2+i]
        gz_latest = get_gyro(GYROData)
        return True
    return False

def DueData(b):
    global yaw, last_time, last_reset, CheckSum, start, data_length

    now = time.time()
    if last_time is None:
        last_time = now

    # 每10秒重置 yaw
    if now - last_reset >= RESET_INTERVAL:
        yaw = 0.0
        last_reset = now

    # 讀取 IMU 資料
    if b == 0x55 and start == 0:
        start = 1
        data_length = 11
        CheckSum = 0
        for i in range(11):
            RxBuff[i] = 0

    if start:
        CheckSum += b
        RxBuff[buf_length-data_length] = b
        data_length -= 1
        if data_length == 0:
            CheckSum = (CheckSum - b) & 0xff
            start = 0
            if GetDataDeal(RxBuff):
                dt = now - last_time
                if abs(gz_latest) > GYRO_THRESHOLD and dt > 0:
                    yaw = (yaw + gz_latest * dt) % 360
                last_time = now
                return yaw
    return None

# 初始化
start = 0
CheckSum = 0
data_length = 0
gz_latest = None

if __name__ == "__main__":
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.5)
    print("Serial opened:", ser.is_open)
    while True:
        b = ser.read(1)
        if not b: continue
        res = DueData(int(b.hex(),16))
        if res is not None:
            print(f"Yaw: {res:.2f}°")
