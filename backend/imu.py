# coding:UTF‑8
# Version: V1.6 — 自動 10 秒硬體偏移校正 for 10‑axis IMU
import serial, math, time

buf_length = 11
RxBuff = [0]*buf_length
ACCData = [0.0]*8; GYROData = [0.0]*8; AngleData = [0.0]*8; MagData = [0.0]*8
acc = [0.0]*3; gyro = [0.0]*3; Angle = [0.0]*3; mag = [0.0]*3
FrameState = CheckSum = start = data_length = 0

# 校正相關變數
is_calibrating = True
calib_start = time.time()
calib_duration = 10  # 校正持續秒數
mx_min = my_min = float('inf')
mx_max = my_max = float('-inf')
bias_x = bias_y = 0.0

def get_acc(datahex):
    # 保留原本的加速度轉換
    axl, axh, ayl, ayh, azl, azh = datahex[:6]
    k_acc = 16.0
    def cv(vh, vl): return (vh<<8 | vl)/32768.0 * k_acc
    ax = cv(axh, axl); ay = cv(ayh, ayl); az = cv(azh, azl)
    for v in (ax, ay, az):
        pass
    return ax, ay, az

def get_gyro(datahex):
    wxl, wxh, wyl, wyh, wzl, wzh = datahex[:6]
    k_gyro = 2000.0
    def cv(vh, vl): return (vh<<8 | vl)/32768.0 * k_gyro
    return cv(wxh, wxl), cv(wyh, wyl), cv(wzh, wzl)

def get_angle(datahex):
    rxl, rxh, ryl, ryh, rzl, rzh = datahex[:6]
    k_ang = 180.0
    def cv(vh, vl): v = (vh<<8 | vl)/32768.0 * k_ang; return v-2*k_ang if v>=k_ang else v
    return cv(rxh, rxl), cv(ryh, ryl), cv(rzh, rzl)

def get_mag(datahex):
    mx = (datahex[1]<<8 | datahex[0]) / 32768.0
    my = (datahex[3]<<8 | datahex[2]) / 32768.0
    mz = (datahex[5]<<8 | datahex[4]) / 32768.0
    mx = mx-2 if mx>=1 else mx
    my = my-2 if my>=1 else my
    mz = mz-2 if mz>=1 else mz
    return mx, my, mz

def compute_heading(mx, my):
    # 補上偏移後直接計算2D heading
    ang = math.degrees(math.atan2(my, mx))
    return (ang + 360) % 360

def update_calibration(mx, my):
    global mx_min, mx_max, my_min, my_max
    mx_min = min(mx_min, mx); mx_max = max(mx_max, mx)
    my_min = min(my_min, my); my_max = max(my_max, my)

def finalize_calibration():
    global bias_x, bias_y, is_calibrating
    bias_x = (mx_max + mx_min) / 2
    bias_y = (my_max + my_min) / 2
    is_calibrating = False
    print(f"🧲 校正完成：bias_x={bias_x:.4f}, bias_y={bias_y:.4f}")

def GetDataDeal(buf):
    global mag
    if buf[-1] != CheckSum: return None
    typ = buf[1]
    if typ == 0x51: acc[:] = get_acc(buf[2:8])
    elif typ == 0x52: gyro[:] = get_gyro(buf[2:8])
    elif typ == 0x53: Angle[:] = get_angle(buf[2:8])
    elif typ == 0x54:
        mag[:] = get_mag(buf[2:8])
        mx, my, mz = mag
        if is_calibrating:
            update_calibration(mx, my)
        else:
            mx_corr, my_corr = mx - bias_x, my - bias_y
            hdg = compute_heading(mx_corr, my_corr)
            return Angle[0], Angle[1], hdg
    return None

def DueData(val):
    global start, CheckSum, data_length
    if val == 0x55 and start == 0:
        start, data_length, CheckSum = 1, buf_length, 0
        RxBuff[:] = [0]*buf_length
    if start:
        CheckSum += val
        RxBuff[buf_length-data_length] = val
        data_length -= 1
        if data_length == 0:
            CheckSum = (CheckSum - val) & 0xff
            start = 0
            return GetDataDeal(RxBuff)
    return None

def main():
    ser = serial.Serial('/dev/imu', 9600, timeout=0.5)
    print("✅ Serial opened:", ser.is_open)
    global is_calibrating
    while True:
        b = ser.read(1)
        if not b: continue
        val = int(b.hex(), 16)
        res = DueData(val)
        if is_calibrating and time.time()-calib_start > calib_duration:
            finalize_calibration()
        if res:
            roll, pitch, heading = res
            print(f"🎯 Roll={roll:.1f}°, Pitch={pitch:.1f}°, Heading={heading:.1f}°")

if __name__ == '__main__':
    main()
