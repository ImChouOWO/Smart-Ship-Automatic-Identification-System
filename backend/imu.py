# coding:UTF-8
# Version: V1.6
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

FrameState = 0
CheckSum = 0
start = 0
data_length = 0

def get_mag(datahex):
    mxl = datahex[0]
    mxh = datahex[1]
    myl = datahex[2]
    myh = datahex[3]
    mzl = datahex[4]
    mzh = datahex[5]
    k_mag = 1.0

    mag_x = (mxh << 8 | mxl) / 32768.0 * k_mag
    mag_y = (myh << 8 | myl) / 32768.0 * k_mag
    mag_z = (mzh << 8 | mzl) / 32768.0 * k_mag

    if mag_x >= k_mag:
        mag_x -= 2 * k_mag
    if mag_y >= k_mag:
        mag_y -= 2 * k_mag
    if mag_z >= k_mag:
        mag_z -= 2 * k_mag

    return mag_x, mag_y, mag_z

def compute_heading(roll, pitch, mag):
    mx, my, mz = mag
    roll_r = math.radians(roll)
    pitch_r = math.radians(pitch)

    Xh = mx * math.cos(pitch_r) + my * math.sin(roll_r) * math.sin(pitch_r) + mz * math.cos(roll_r) * math.sin(pitch_r)
    Yh = my * math.cos(roll_r) - mz * math.sin(roll_r)

    hdg = (math.degrees(math.atan2(Yh, Xh)) + 360) % 360
    return hdg

def GetDataDeal(list_buf):
    global acc, gyro, Angle, mag

    if(list_buf[buf_length - 1] != CheckSum):
        return None

    if(list_buf[1] == 0x51):
        for i in range(6):
            ACCData[i] = list_buf[2+i]
        acc = get_acc(ACCData)

    elif(list_buf[1] == 0x52):
        for i in range(6):
            GYROData[i] = list_buf[2+i]
        gyro = get_gyro(GYROData)

    elif(list_buf[1] == 0x53):
        for i in range(6):
            AngleData[i] = list_buf[2+i]
        Angle = get_angle(AngleData)

    elif(list_buf[1] == 0x54):
        for i in range(6):
            MagData[i] = list_buf[2+i]
        mag = get_mag(MagData)

    # ➕ 新增 heading 計算
    heading = compute_heading(Angle[0], Angle[1], mag)
    return Angle[0], Angle[1], heading


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
    axl = datahex[0]
    axh = datahex[1]
    ayl = datahex[2]
    ayh = datahex[3]
    azl = datahex[4]
    azh = datahex[5]
    k_acc = 16.0
    acc_x = (axh << 8 | axl) / 32768.0 * k_acc
    acc_y = (ayh << 8 | ayl) / 32768.0 * k_acc
    acc_z = (azh << 8 | azl) / 32768.0 * k_acc
    if acc_x >= k_acc:
        acc_x -= 2 * k_acc
    if acc_y >= k_acc:
        acc_y -= 2 * k_acc
    if acc_z >= k_acc:
        acc_z -= 2 * k_acc
    return acc_x, acc_y, acc_z

def get_gyro(datahex):
    wxl = datahex[0]
    wxh = datahex[1]
    wyl = datahex[2]
    wyh = datahex[3]
    wzl = datahex[4]
    wzh = datahex[5]
    k_gyro = 2000.0
    gyro_x = (wxh << 8 | wxl) / 32768.0 * k_gyro
    gyro_y = (wyh << 8 | wyl) / 32768.0 * k_gyro
    gyro_z = (wzh << 8 | wzl) / 32768.0 * k_gyro
    if gyro_x >= k_gyro:
        gyro_x -= 2 * k_gyro
    if gyro_y >= k_gyro:
        gyro_y -= 2 * k_gyro
    if gyro_z >= k_gyro:
        gyro_z -= 2 * k_gyro
    return gyro_x, gyro_y, gyro_z

def get_angle(datahex):
    rxl = datahex[0]
    rxh = datahex[1]
    ryl = datahex[2]
    ryh = datahex[3]
    rzl = datahex[4]
    rzh = datahex[5]
    k_angle = 180.0
    angle_x = (rxh << 8 | rxl) / 32768.0 * k_angle
    angle_y = (ryh << 8 | ryl) / 32768.0 * k_angle
    angle_z = (rzh << 8 | rzl) / 32768.0 * k_angle
    if angle_x >= k_angle:
        angle_x -= 2 * k_angle
    if angle_y >= k_angle:
        angle_y -= 2 * k_angle
    if angle_z >= k_angle:
        angle_z -= 2 * k_angle
    return angle_x, angle_y, angle_z



if __name__ == '__main__':
    port = '/dev/ttyUSB0'  # Linux
    # port = 'COM12'        # Windows
    baud = 9600
    ser = serial.Serial(port, baud, timeout=0.5)
    print("Serial is Opened:", ser.is_open)
    while True:
        RXdata = ser.read(1)
        if RXdata:
            RXdata = int(RXdata.hex(), 16)
            DueData(RXdata)
