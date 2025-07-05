# imu_set_baud_115200.py
import serial
import time

# 設定參數
PORT = '/dev/imu'   # 依實際使用的 port 調整
OLD_BAUD = 9600
NEW_BAUD = 115200

# 設定封包
SET_BAUD_115200 = bytes([0xFF, 0xAA, 0x04, 0x06])
SAVE_CONFIG = bytes([0xFF, 0xAA, 0x00, 0x00])

def open_serial(port, baud):
    try:
        ser = serial.Serial(port, baud, timeout=0.5)
        print(f"✅ Serial opened at {baud} bps")
        return ser
    except Exception as e:
        print(f"❌ Failed to open serial at {baud}: {e}")
        return None

def main():
    print("🛠️ Step 1: 連接 IMU 並傳送設定 Baudrate 指令...")
    ser = open_serial(PORT, OLD_BAUD)
    if not ser:
        return

    print("📤 發送：設為 115200 bps")
    ser.write(SET_BAUD_115200)
    time.sleep(1)
    ser.close()

    print("⏳ 等待切換完成，重新連線為 115200")
    time.sleep(1)

    ser = open_serial(PORT, NEW_BAUD)
    if not ser:
        return

    print("📤 發送：儲存設定（EEPROM）")
    ser.write(SAVE_CONFIG)

    print("🧪 測試是否收到封包...")
    time.sleep(1)
    for _ in range(20):
        data = ser.read(11)
        if data and data[0] == 0x55:
            print(f"📥 成功收到封包：{' '.join(f'{b:02X}' for b in data)}")
            break
        time.sleep(0.1)
    else:
        print("⚠️ 未收到正確封包，請確認是否成功設置")

    ser.close()
    print("✅ 結束，IMU 現在使用 115200 bps 通訊")

if __name__ == '__main__':
    main()
