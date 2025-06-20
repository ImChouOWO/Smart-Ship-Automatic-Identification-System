import time
import serial

# BCC 計算函數
def calculate_bcc(data):
    bcc = 0
    for byte in data:
        bcc ^= byte
    return bcc

# 設定 serial port（依照你的實際設備調整）
ser = serial.Serial('/dev/ttyUSB4', 9600, timeout=1)

# 定義封包組成資料
def build_packet():
    header = 0x1B
    command = 0x01
    sequence = 0x01
    opcode = 0x09
    speed = 0x42
    separator = 0x7C
    direction = 0x42
    send_role = 0x02
    receive_role = 0x01
    length = 0x03

    packet = [header, command, sequence, opcode, length,
              speed, separator, direction, send_role, receive_role]
    bcc = calculate_bcc(packet)
    packet.append(bcc)
    return bytearray(packet)

# 每秒發送一次封包
try:
    while True:
        packet = build_packet()
        ser.write(packet)
        print(f'Sent: {[hex(b) for b in packet]}')
        time.sleep(1)

except KeyboardInterrupt:
    print("❗ 中斷傳輸")
finally:
    ser.close()
