# coding:UTF-8
# Version: V1.5.1
import serial

buf_length = 11
RxBuff = [0]*buf_length

ACCData = [0.0]*8
GYROData = [0.0]*8
AngleData = [0.0]*8
FrameState = 0  # 判斷狀態
CheckSum = 0  # 校驗碼

start = 0  # 是否遇到封包開頭
data_length = 0  # 封包長度

acc = [0.0]*3
gyro = [0.0]*3
Angle = [0.0]*3

def GetDataDeal(list_buf):
    global acc, gyro, Angle
    if list_buf[buf_length - 1] != CheckSum:  # 校驗失敗
        return

    if list_buf[1] == 0x51:  # 加速度
        for i in range(6):
            ACCData[i] = list_buf[2+i]
        acc = get_acc(ACCData)

    elif list_buf[1] == 0x52:  # 角速度
        for i in range(6):
            GYROData[i] = list_buf[2+i]
        gyro = get_gyro(GYROData)

    elif list_buf[1] == 0x53:  # 姿態角 (歐拉角)
        for i in range(6):
            AngleData[i] = list_buf[2+i]
        Angle = get_angle(AngleData)

        # 假設偏移角為 20 度，修正 heading（Yaw 為 Z 軸）
        heading = (Angle[2] - 20 + 360) % 360

        print("acc   : %10.3f %10.3f %10.3f" % (acc[0], acc[1], acc[2]))
        print("gyro  : %10.3f %10.3f %10.3f" % (gyro[0], gyro[1], gyro[2]))
        print("angle : %10.3f %10.3f %10.3f" % (Angle[0], Angle[1], Angle[2]))
        print("heading after offset : %.2f\n" % heading)

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
    # 歐拉角 (Roll, Pitch, Yaw)
    roll  = to_signed(datahex[1] << 8 | datahex[0]) / 32768.0 * 180.0
    pitch = to_signed(datahex[3] << 8 | datahex[2]) / 32768.0 * 180.0
    yaw   = to_signed(datahex[5] << 8 | datahex[4]) / 32768.0 * 180.0
    return roll, pitch, yaw

if __name__ == '__main__':
    port = '/dev/ttyUSB0'  # 若為 Jetson 或 Linux
    baud = 9600  # 可改為 115200 / 921600（需看你的模組支援）
    ser = serial.Serial(port, baud, timeout=0.5)
    print("✅ 串口開啟成功:", ser.is_open)
    while True:
        RXdata = ser.read(1)
        if RXdata:
            RXdata = int(RXdata.hex(), 16)
            DueData(RXdata)
