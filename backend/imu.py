# coding:UTF-8
# Version: V1.5.1
import serial

buf_length = 11
RxBuff = [0]*buf_length

ACCData = [0.0]*8
GYROData = [0.0]*8
AngleData = [0.0]*8

start = 0
data_length = 0
CheckSum = 0

acc = [0.0]*3
gyro = [0.0]*3
Angle = [0.0]*3

yaw_0 = None  # 初始 yaw 校正角度（相對 heading 參考）

def GetDataDeal(list_buf):
    global acc, gyro, Angle, yaw_0

    if list_buf[buf_length - 1] != CheckSum:
        return None

    if list_buf[1] == 0x51:
        for i in range(6): 
            ACCData[i] = list_buf[2+i]
        acc = get_acc(ACCData)

    elif list_buf[1] == 0x52:
        for i in range(6): 
            GYROData[i] = list_buf[2+i]
        gyro = get_gyro(GYROData)

    elif list_buf[1] == 0x53:
        for i in range(6): 
            AngleData[i] = list_buf[2+i]
        Angle = get_angle(AngleData)

        # ➕ 相對 heading 校正邏輯
        yaw_now = Angle[2]
        if yaw_0 is None:
            yaw_0 = yaw_now
            print(f"📍 設定初始朝向 yaw_0 = {yaw_0:.2f}°")
            relative_yaw = 0.0
        else:
            relative_yaw = ((yaw_now - yaw_0 + 540) % 360) - 180

        return (Angle[0], Angle[1], relative_yaw)  # 傳回 roll, pitch, 校正後的 yaw

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
            CheckSum = (CheckSum - inputdata) & 0xFF
            start = 0
            return GetDataDeal(RxBuff)

def get_acc(datahex):
    def decode(u8_l, u8_h):
        raw = int.from_bytes([u8_l, u8_h], byteorder='little', signed=True)
        return raw / 32768.0 * 16.0
    return decode(datahex[0], datahex[1]), decode(datahex[2], datahex[3]), decode(datahex[4], datahex[5])

def get_gyro(datahex):
    def decode(u8_l, u8_h):
        raw = int.from_bytes([u8_l, u8_h], byteorder='little', signed=True)
        return raw / 32768.0 * 2000.0
    return decode(datahex[0], datahex[1]), decode(datahex[2], datahex[3]), decode(datahex[4], datahex[5])

def get_angle(datahex):
    def decode(u8_l, u8_h):
        raw = int.from_bytes([u8_l, u8_h], byteorder='little', signed=True)
        return raw / 32768.0 * 180.0
    return decode(datahex[0], datahex[1]), decode(datahex[2], datahex[3]), decode(datahex[4], datahex[5])

# 測試主函數
if __name__ == '__main__':
    port = '/dev/imu'  # Linux serial port
    baud = 9600
    ser = serial.Serial(port, baud, timeout=0.5)
    print("✅ Serial is Opened:", ser.is_open)

    while True:
        RXdata = ser.read(1)
        if RXdata:
            byte_val = int.from_bytes(RXdata, byteorder='big')
            result = DueData(byte_val)
            if result:
                roll, pitch, yaw = result
                print(f"📈 Roll: {roll:.2f}°, Pitch: {pitch:.2f}°, Relative Yaw: {yaw:.2f}°")
