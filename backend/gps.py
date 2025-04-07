import serial
import time

def parse_nmea_sentence(sentence):
    if sentence.startswith('$GPGGA'):
        parts = sentence.split(',')
        if len(parts) > 6 and parts[6] == '1':
            time_str = parts[1]
            lat = parts[2]
            lat_dir = parts[3]
            lon = parts[4]
            lon_dir = parts[5]
            alt = parts[9]
            return time_str, lat, lat_dir, lon, lon_dir, alt
    return None, None, None, None, None, None

port = "/dev/ttyACM0"
ser = serial.Serial(port, baudrate=4800, timeout=5)

while True:
    try:
        line = ser.readline().decode('ascii', errors='replace').strip()
        if line:
            print(f"接收到的NMEA語句: {line}")
            time_str, lat, lat_dir, lon, lon_dir, alt = parse_nmea_sentence(line)
            if time_str and lat and lon:
                print(f"時間: {time_str}")
                print(f"緯度: {lat} {lat_dir}")
                print(f"經度: {lon} {lon_dir}")
                print(f"海拔: {alt} M")
                break  # 成功接收到有效數據後退出迴圈
            else:
                print("無效的NMEA數據，繼續等待...")
    except KeyboardInterrupt:
        print("程式中斷")
        break
    except Exception as e:
        print(f"讀取錯誤: {e}")
        break

ser.close()