# coding: UTF-8
# Version: V1.5.1 - Modified for Yaw → Heading
import serial

buf_length = 11
RxBuff = [0] * buf_length

ACCData = [0.0] * 8
GYROData = [0.0] * 8
AngleData = [0.0] * 8
FrameState = 0
CheckSum = 0

start = 0
data_length = 0

acc = [0.0] * 3
gyro = [0.0] * 3
Angle = [0.0] * 3

# 可手動設定偏移角（例如校準時記下某一方向為正北）
HEADING_OFFSET = 0  # 若你北方為 +10 度，設為 -10 即可對齊

def GetDataDeal(list_buf):
    global acc, gyro, Angle

    if list_buf[buf_length - 1] != CheckSum:
        return

    if list_buf[1] == 0x51:
        for i in range(6):
            ACCData[i] = list_buf[2 + i]
        acc = get_acc(ACCData)

    elif list_buf[1] == 0x52:
        for i in range(6):
            GYROData[i] = list_buf[2 + i]
        gyro = get_gyro(GYROData)

    elif list_buf[1] == 0x53:
        for i in range(6):
            AngleData[i] = list_buf[2 + i]
        Angle = get_angle(AngleData)

        # === 將 Yaw 轉為 Heading（加 offset 並映射至 0~360） ===
        raw_yaw = Angle[2]
        heading = (raw_yaw + HEADING_OFFSET + 360) % 360

        print("加速度 acc   : %10.3f %10.3f %10.3f" % tuple(acc))
        print("角速度 gyro  : %10.3f %10.3f %10.3f" % tuple(gyro))
        print("歐拉角 angle : %10.3f %10.3f %10.3f" % tuple(Angle))
        print("➡️ Heading   : %.2f°\n" % heading)


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
            CheckSum = (CheckSum - inputdata) & 0xFF
            start = 0
            GetDataDeal(RxBuff)


def to_signed(val):
    return val - 65536 if val > 32767 else val


def get_acc(datahex):
    ax = to_signed(datahex[1] << 8 | datahex[0]) / 32768.0 * 16.0
    ay = to_signed(datahex[3] << 8 | datahex[2]) / 32768.0 * 16.0
    az = to_signed(datahex[5] << 8 | datahex[4]) / 32768.0 * 16.0
    return ax, ay, az


def get_gyro(datahex):
    gx = to_signed(datahex[1] << 8 | datahex[0]) / 32768.0 * 2000.0
    gy = to_signed(datahex[3] << 8 | datahex[2]) / 32768.0 * 2000.0
    gz = to_signed(datahex[5] << 8 | datahex[4]) / 32768.0 * 2000.0
    return gx, gy, gz


def get_angle(datahex):
    roll = to_signed(datahex[1] << 8 | datahex[0]) / 32768.0 * 180.0
    pitch = to_signed(datahex[3] << 8 | datahex[2]) / 32768.0 * 180.0
    yaw = to_signed(datahex[5] << 8 | datahex[4]) / 32768.0 * 180.0
    return roll, pitch, yaw


if __name__ == '__main__':
    port = '/dev/imu'  # Linux 或 Jetson 裝置的 USB 端口
    baud = 9600  # 或依模組支援改為 115200 或 921600
    ser = serial.Serial(port, baud, timeout=0.5)
    print("✅ 串口開啟成功:", ser.is_open)

    while True:
        RXdata = ser.read(1)
        if RXdata:
            RXdata = int(RXdata.hex(), 16)
            DueData(RXdata)
