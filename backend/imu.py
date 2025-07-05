# coding:UTF-8
# Version: V1.6.1
import serial
import math

buf_length = 11
RxBuff = [0]*buf_length

ACCData = [0.0]*8
GYROData = [0.0]*8
AngleData = [0.0]*8
MagData = [0.0]*8

acc = [0.0]*3
gyro = [0.0]*3
Angle = [0.0]*3
mag = [0.0]*3

CheckSum = 0
start = 0
data_length = 0

latest_roll = None
latest_pitch = None
latest_mag = None
initial_heading = None  # 🧭 初始朝向，用來計算相對 heading

def get_mag(datahex):
    mxl, mxh, myl, myh, mzl, mzh = datahex
    k_mag = 1.0
    mx = (mxh << 8 | mxl) / 32768.0 * k_mag
    my = (myh << 8 | myl) / 32768.0 * k_mag
    mz = (mzh << 8 | mzl) / 32768.0 * k_mag
    if mx >= k_mag: mx -= 2 * k_mag
    if my >= k_mag: my -= 2 * k_mag
    if mz >= k_mag: mz -= 2 * k_mag
    return mx, my, mz

def compute_heading(roll, pitch, mag):
    mx, my, mz = mag
    roll_r = math.radians(roll)
    pitch_r = math.radians(pitch)

    # 傾角補償
    Xh = mx * math.cos(pitch_r) + my * math.sin(roll_r) * math.sin(pitch_r) + mz * math.cos(roll_r) * math.sin(pitch_r)
    Yh = my * math.cos(roll_r) - mz * math.sin(roll_r)

    # 原始 heading
    hdg = math.degrees(math.atan2(Yh, Xh))

    # 加入磁場偏差校正（依你現場量測設定）
    heading_offset = 190.0  # ✅ 若北偏 190°，請設為 190.0
    hdg = (hdg - heading_offset + 360) % 360

    return hdg

def GetDataDeal(list_buf):
    global acc, gyro, Angle, mag
    global latest_roll, latest_pitch, latest_mag, initial_heading

    if list_buf[buf_length - 1] != CheckSum:
        return None

    if list_buf[1] == 0x51:
        acc = get_acc(list_buf[2:8])

    elif list_buf[1] == 0x52:
        gyro = get_gyro(list_buf[2:8])

    elif list_buf[1] == 0x53:
        Angle = get_angle(list_buf[2:8])
        latest_roll, latest_pitch = Angle[0], Angle[1]

    elif list_buf[1] == 0x54:
        mag = get_mag(list_buf[2:8])
        latest_mag = mag

    if latest_roll is not None and latest_pitch is not None and latest_mag is not None:
        heading = compute_heading(latest_roll, latest_pitch, latest_mag)

        # ➕ 設定開機基準 heading 為 0
        if initial_heading is None:
            initial_heading = heading
            print(f"📍 設定初始方向為 {initial_heading:.2f}°")

        # 計算相對 heading（左右偏轉）
        relative_heading = ((heading - initial_heading + 540) % 360) - 180

        return latest_roll, latest_pitch, heading, relative_heading

    return None

def DueData(inputdata):
    global start, CheckSum, data_length
    if inputdata == 0x55 and start == 0:
        start = 1
        data_length = 11
        CheckSum = 0
        for i in range(11):
            RxBuff[i] = 0

    if start == 1:
        CheckSum += inputdata
        RxBuff[buf_length - data_length] = inputdata
        data_length -= 1
        if data_length == 0:
            CheckSum = (CheckSum - inputdata) & 0xff
            start = 0
            return GetDataDeal(RxBuff)

def get_acc(datahex):
    return tuple(decode(datahex[i], datahex[i+1], 16.0) for i in range(0, 6, 2))

def get_gyro(datahex):
    return tuple(decode(datahex[i], datahex[i+1], 2000.0) for i in range(0, 6, 2))

def get_angle(datahex):
    return tuple(decode(datahex[i], datahex[i+1], 180.0) for i in range(0, 6, 2))

def decode(low, high, scale):
    raw = int.from_bytes([low, high], byteorder='little', signed=True)
    return raw / 32768.0 * scale

# 主程式入口
if __name__ == '__main__':
    port = '/dev/imu'  # ✅ 根據你裝置修改
    baud = 9600
    ser = serial.Serial(port, baud, timeout=0.5)
    print("✅ Serial is Opened:", ser.is_open)

    while True:
        RXdata = ser.read(1)
        if RXdata:
            RXdata = int(RXdata.hex(), 16)
            result = DueData(RXdata)
            if result:
                roll, pitch, heading, rel_heading = result
                print(f"✅ Roll: {roll:.2f}°  Pitch: {pitch:.2f}°  Heading: {heading:.2f}°  Relative: {rel_heading:.2f}°")
