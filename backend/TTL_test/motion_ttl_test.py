import serial
import time
import threading

# 串列埠設定（請依你的實際設備修改）
ser = serial.Serial(port='/dev/ttyUSB4', baudrate=9600)  # ← 修改為你的 COM port

# 計算 packet 的 BCC
def calculate_bcc(data):
    bcc = 0
    for byte in data:
        bcc ^= byte
    return bcc

# 生成單次封包資料
def generate_packet():
    header = 0x1B
    command = 0x04
    sequence = 0x01
    opcode = 0x01

    # 經緯度（緯度在前，經度在後）
    latitude_bytes  = [0x03, 0xD2, 0x27]     # = 0.250023
    longitude_bytes = [0x12, 0x8F, 0xC5]     # = 1.222597
    separator = 0x7C

    speed = 0x09
    direction = 0x02
    timestamp = [0x0E, 0x20, 0x11]
    send_role = 0x01
    receive_role = 0x03

    data = (
        latitude_bytes + [separator] +
        longitude_bytes + [separator] +
        [speed, separator, direction] +
        timestamp
    )

    length = len(data)

    packet = [
        header, command, sequence, opcode, length
    ] + data + [send_role, receive_role]

    bcc = calculate_bcc(packet)
    packet.append(bcc)

    # 選擇性加上結尾標記（如 0x6E）供 Arduino 做分包顯示
    packet.append(0x6E)

    return packet

def send_packet():
    while True:
        packet = generate_packet()
        ser.write(bytearray(packet))
        print("📤 傳送封包:", ' '.join(f'0x{b:02X}' for b in packet))
        time.sleep(0.5)  # 每秒傳送一次

def receive_packet():
    PACKET_LEN = 11
    buffer = bytearray()
    while True:
        if ser.in_waiting:
            buffer += ser.read(ser.in_waiting)

            while len(buffer) >= PACKET_LEN:
                packet = buffer[:PACKET_LEN]
                buffer = buffer[PACKET_LEN:]

                data = packet[:-1]
                received_bcc = packet[-1]
                calculated_bcc = calculate_bcc(data)

                print("📥 接收封包:", ' '.join(f'0x{b:02X}' for b in packet))

                if received_bcc != calculated_bcc:
                    print(f"❌ BCC 錯誤：接收 {hex(received_bcc)} ≠ 計算 {hex(calculated_bcc)}\n")
                else:
                    print("✅ BCC 驗證成功\n")

# === 主傳送迴圈 ===
try:
    while True:
        threading.Thread(target=send_packet, daemon=True)
        threading.Thread(target=receive_packet, daemon=True)

except KeyboardInterrupt:
    print("⛔ 傳送中止")
    ser.close()