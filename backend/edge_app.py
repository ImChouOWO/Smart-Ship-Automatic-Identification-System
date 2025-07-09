import subprocess
import socketio
import time
import os
from imu import DueData
import lidar
from multiprocessing import Process, Manager
import multiprocessing
import serial
from datetime import datetime
import threading
import yaml



SERVER_URL = None

#Streaming URL
RTSP_URL = None

#TTL Port and Baudrate
VIDEO_DEVICE = None
IMU = None
LIDAR = None
GPS = None
POWER_SER = None
MOTION_SER = None
BAUDRATE = None



#check motion and power sockectio connect
#It will rerender system status on front
MOTION_CONNECT = False
POWER_CONNECT =False

#initial packet
FIRST_SEND = True
NOW_SPEED =None
NOW_DIRECTION = None

#Sending it to power system when it not none  
POWER_PACKET =None
LAST_VALID_PACKET = None

def load_config(path="config.yaml"):
    global SERVER_URL, RTSP_URL
    global VIDEO_DEVICE, IMU, LIDAR, GPS, POWER_SER, MOTION_SER, BAUDRATE

    with open(path, "r") as f:
        cfg = yaml.safe_load(f)

    SERVER_URL = cfg['SERVER_URL']['ip']
    RTSP_URL = cfg['RTSP_URL']['ip']

    VIDEO_DEVICE = cfg['sensor']['video']
    IMU = cfg['sensor']['imu']
    LIDAR = cfg['sensor']['lidar']
    GPS = cfg['sensor']['gps']
    POWER_SER = cfg['sensor']['power_ser']
    MOTION_SER = cfg['sensor']['motion_ser']
    BAUDRATE = cfg['sensor']['baudrate']


def sio_connecter(sio, timeout=0.5):
    result = {"success": False}

    def connect_thread():
        try:
            sio.connect(SERVER_URL)
            result["success"] = True
        except Exception as e:
            print(f"❌ SocketIO connect exception: {e}")

    t = threading.Thread(target=connect_thread)
    t.start()
    t.join(timeout)

    if t.is_alive():
        print("❌ SocketIO connect timeout.")
        return None

    return sio if result["success"] else None

def create_resilient_sio(name="module"):
    print(f"🔌 [{name}] Connecting to SocketIO server...")
    sio = socketio.Client(
        reconnection=True,
        reconnection_attempts=1,
        reconnection_delay=0.1
    )

    @sio.event
    def connect():
        print(f"✅ [{name}] SocketIO Connected")

    @sio.event
    def disconnect():
        print(f"❌ [{name}] SocketIO Disconnected")

    sio = sio_connecter(sio, timeout=0.1)

    if sio is None or not sio.connected:
        print(f"⚠️ [{name}] SocketIO connection failed or not connected")
        return None

    return sio


def lidar_callback(scan_results, sio):
    send_data = [{"angle": round(a, 2), "dist": round(d, 2), "q": q} for a, d, q in scan_results[:100]]
    if sio.connected:
        sio.emit("get_lidar", send_data)
        # print(f"📤 Sent {len(send_data)} lidar points")
    else:
        print("⚠️ LiDAR SocketIO disconnected, skipping emit.")

def lidar_process_func():
    lidar.PORT = LIDAR
    lidar.BAUDRATE = 1000000
    sio = create_resilient_sio("LIDAR")

    while True:
        try:
            lidar.start_lidar_scan(callback=lambda data: lidar_callback(data, sio))
        except Exception as e:
            print(f"❌ LiDAR process error: {e}")
            time.sleep(0.01)

def imu_process_func(shared_imu):
    port = IMU
    baud = 9600
    sio =None
    ser = None
    while True:
        try:
            ser = serial.Serial(port, baud, timeout=0.5)
            print("✅ IMU Serial Opened:", ser.is_open)
        except:
            ser = None
            print("IMU Serial Opened Fail")
        if ser is not None:
            if ser.is_open:
                break
        time.sleep(1)            

    try:
        
        time.sleep(0.01)

        while True:
            

            RXdata = ser.read(1)
            if not RXdata:
                continue

            try:
                value = int(RXdata.hex(), 16)
            except ValueError:
                continue

            result = DueData(value)
            if result:
                imu_data = ['%.3f' % result[0], '%.3f' % result[1], '%.3f' % (result[2] - 167)]
                shared_imu['rpy'] = imu_data
                try:
                    if sio is None or not sio.connected:
                        print("🔁 IMU SocketIO lost. Reconnecting...")
                        sio = create_resilient_sio("IMU")
                        continue
                    if sio.connected:
                        sio.emit("get_imu", imu_data)
                        # print(f"📤 Sent IMU data: {imu_data}")
                except Exception as e:
                    print(f"❌ IMU emit error: {e}")
                    time.sleep(1)

    except Exception as e:
        print(f"❌ IMU process fatal error: {e}")
        time.sleep(0.1)

def parse_nmea_gpgga(sentence):
    if sentence.startswith('$GPGGA'):
        parts = sentence.split(',')
        if len(parts) >= 10 and parts[6] != '0':
            time_str = parts[1]
            lat_raw, lat_dir = parts[2], parts[3]
            lon_raw, lon_dir = parts[4], parts[5]
            alt = parts[9]

            try:
                lat_deg = float(lat_raw[:2]) + float(lat_raw[2:]) / 60.0
                if lat_dir == 'S':
                    lat_deg *= -1

                lon_deg = float(lon_raw[:3]) + float(lon_raw[3:]) / 60.0
                if lon_dir == 'W':
                    lon_deg *= -1

                return time_str, lat_deg, lon_deg, float(alt)
            except ValueError:
                return None, None, None, None
    return None, None, None, None

def gps_process_func(shared_gps):
    port = GPS
    baud = 4800
    sio = None
    ser = None
    while True:
        try:
            ser = serial.Serial(port, baud, timeout=0.5)
            print("✅ GPS Serial Opened:", ser.is_open)
        
        except:
            ser = None
            print("GPS Serial Opened Fail")
        if ser is not None:
            if ser.is_open:
                break
        time.sleep(1)

    try:
       
        time.sleep(0.01)
        last_data = {
            "time": "",
            "latitude": 0.0,
            "longitude": 0.0,
            "altitude": 0.0
        }
        while True:
            

            try:
                line = ser.readline().decode('ascii', errors='replace').strip()
                if line:
                    # print(f"📥 NMEA: {line}")
                    time_str, lat, lon, alt = parse_nmea_gpgga(line)
                    if time_str and lat and lon:
                        
                        last_data = {
                            "time": time_str,
                            "latitude": lat,
                            "longitude": lon,
                            "altitude": alt
                        }
                    shared_gps['time'] = last_data["time"]
                    shared_gps['latitude'] = last_data["latitude"]
                    shared_gps['longitude'] = last_data["longitude"]
                    shared_gps['altitude'] = last_data["altitude"]
                        
                    try:
                        if sio is None or not sio.connected:
                            print("🔁 GPS SocketIO lost. Reconnecting...")
                            sio = create_resilient_sio("GPS")
                            continue
                        if sio.connected:
                            sio.emit("get_gps", last_data)
                            # print(f"📤 Sent GPS data: {last_data}")
                    except Exception as e:
                        print(f"❌ GPS emit error: {e}")
                    # else:
                    #     print("⚠️ GPGGA 無有效座標")
            except Exception as e:
                print(f"❌ GPS parse error: {e}")
                time.sleep(0.01)
    except Exception as e:
        print(f"❌ GPS Serial connect error: {e}")
        time.sleep(0.01)
def controller_process_func(shared_imu, shared_gps):
    global POWER_PACKET, LAST_VALID_PACKET
    motion_port = MOTION_SER
    power_port = POWER_SER
    baud = BAUDRATE
    motion_ser =None
    power_ser = None
    sio = None
    while True:
        try:
            motion_ser = serial.Serial(port=motion_port, baudrate=baud, timeout=0.001)
            print("✅ Motion Controller Serial Opened:", motion_ser.is_open)
        except:
            motion_ser =None
            print("Open Motion Serial Fail")

        try:
            power_ser = serial.Serial(port=power_port, baudrate=baud, timeout=0.001)
            print("✅ Power Controller Serial Opened:", power_ser.is_open)
        except:
            power_ser = None
            print("Open Power Serial Fail")

        if power_ser is not None and motion_ser is not None :
            if power_ser.is_open and motion_ser.is_open:
                print("✅ Both Motion and Power Serial are open")
                break

        time.sleep(1)

   
    
    

    

    while True:
        try:

            POWER_PACKET = connect_to_motion(motion_ser, shared_imu, shared_gps)
            print("POWER_PACKET:", POWER_PACKET)
            if POWER_PACKET is not None:
                connect_to_power(power_ser, POWER_PACKET)
                LAST_VALID_PACKET = POWER_PACKET
            else:
                connect_to_power(power_ser, LAST_VALID_PACKET)
            time.sleep(0.5)
            
            if sio is None or not sio.connected:
                sio = create_resilient_sio("motion_power TTL")
                continue  # 不要送封包
            sio.emit("get_ttl_info", {"motion": MOTION_CONNECT, "power": POWER_CONNECT})
            
        except Exception as e:
            print(f"❌ Controller process error: {e}")
            time.sleep(0.5)
    
def calculate_bcc(data):
    bcc = 0
    for byte in data:
        bcc ^= byte
    return bcc

def connect_to_motion(motion_ser, shared_imu, shared_gps):
    global MOTION_CONNECT
    try:

        rpy = shared_imu.get('rpy', [0.0, 0.0, 0.0])
        roll = float(rpy[0])
        pitch = float(rpy[1])
        yaw = float(rpy[2])

        lat = shared_gps.get('latitude', 0.0)
        lon = shared_gps.get('longitude', 0.0)
        packet = generate_packet(lat, lon, roll, pitch, yaw)
        packet = send_recive_data(packet, motion_ser)
        if packet is not None:
            MOTION_CONNECT =True
            return packet
        else:
            MOTION_CONNECT = False
            print("❌ 無法接收Motion 封包")
            return None

    except Exception as e:
        print(f"❌ Motion Serial connect error: {e}")
        return None
    
def generate_packet(lat, lon, roll, pitch, yaw):
    header = 0x1B
    command = 0x04
    sequence = 0x01
    opcode = 0x01
    separator = 0x7C
    # 系統時間轉為 [hour, minute, second]
    now = datetime.now()
    timestamp = [now.hour & 0xFF, now.minute & 0xFF, now.second & 0xFF]
    
    send_role = 0x01
    receive_role = 0x03

    # Encode lat/lon to 3 bytes (大端)
    lat_raw = int(lat * 10000)
    lon_raw = int(lon * 10000)
    lat_bytes = [(lat_raw >> 16) & 0xFF, (lat_raw >> 8) & 0xFF, lat_raw & 0xFF]
    lon_bytes = [(lon_raw >> 16) & 0xFF, (lon_raw >> 8) & 0xFF, lon_raw & 0xFF]

    # Encode IMU (roll, pitch, yaw) to 2 bytes each
    roll_raw = int(roll * 1000)
    pitch_raw = int(pitch * 1000)
    yaw_raw = int(yaw * 1000)
    roll_bytes = [(roll_raw >> 8) & 0xFF, roll_raw & 0xFF]
    pitch_bytes = [(pitch_raw >> 8) & 0xFF, pitch_raw & 0xFF]
    yaw_bytes = [(yaw_raw >> 8) & 0xFF, yaw_raw & 0xFF]

    # FIRST_SEND 判斷速度與方向
    global FIRST_SEND, NOW_SPEED, NOW_DIRECTION
    if FIRST_SEND:
        speed = 0x00
        direction = 0x42
    else:
        speed = NOW_SPEED or 0x00
        direction = NOW_DIRECTION or 0x00

    # 正確封包組裝
    data = (
        lat_bytes + [separator] +
        lon_bytes + [separator] +
        [speed, separator, direction, separator] +
        roll_bytes + [separator] + pitch_bytes + [separator] + yaw_bytes +
        timestamp
    )

    length = len(data)
    packet = [header, command, sequence, opcode, length] + data + [send_role, receive_role]
    bcc = calculate_bcc(packet)
    packet.append(bcc)
    return packet

    
def receive_packet(motion_ser):
        """
        讀取並解析來自 motion_ser 的封包，返回完整的封包 (bytes)，
        並從緩衝區中移除已處理的 bytes。
        若暫無完整封包，回傳 None。
        """
        PACKET_LEN = 11
        HEADER_BYTE = 0x1B
        global NOW_SPEED, NOW_DIRECTION
        # 使用函式屬性做持久化緩衝區
        buf = getattr(receive_packet, '_buffer', bytearray())
        # 讀取所有可用資料
        if motion_ser.in_waiting:
            buf += motion_ser.read(motion_ser.in_waiting)
        # 更新緩衝區
        receive_packet._buffer = buf

        # 循環嘗試解析完整封包
        while len(buf) >= PACKET_LEN:
            # 對齊到 HEADER
            if buf[0] != HEADER_BYTE:
                buf.pop(0)
                continue
            # 擷取可能的封包
            packet = bytes(buf[:PACKET_LEN])
            data = packet[:-1]
            received_bcc = packet[-1]
            if received_bcc != calculate_bcc(data):
                # BCC 錯誤，移除首位後重試
                buf.pop(0)
                continue
            # 成功解析，移除已處理 bytes
            del buf[:PACKET_LEN]
            receive_packet._buffer = buf
            print("📥 接收封包:", ' '.join(f'0x{b:02X}' for b in packet))
            print("✅ BCC 驗證成功")
            NOW_SPEED = packet[5]
            NOW_DIRECTION = packet[7]
            return packet
        # 無完整封包
        return None
    
    
def send_recive_data(packet, motion_ser):

        global FIRST_SEND

        if packet != None:
            motion_ser.write(bytearray(packet))
            packet = receive_packet(motion_ser)
            FIRST_SEND = False
            print("Send to motion")
            return packet
            
            
        else:
            print("No data can send to motion system")
            return None
   

def connect_to_power(power_ser, packet):
    global POWER_CONNECT
    if packet is None:
        print("❌ 無法接收 Motion 封包")
        return
    try:
        if power_ser.is_open:
            POWER_CONNECT = True
            print("✅ Power Serial 已開啟")
            send_to_power(power_ser, packet)
        else:
            POWER_CONNECT = False
    except Exception as e: 
        print(f"❌ Power Serial 開啟失敗: {e}")
        return
    
def send_to_power(power_ser, packet):
    try:
        power_ser.write(bytearray(packet))
        print("📤 發送封包到 Power Controller:", ' '.join(f'0x{b:02X}' for b in packet))
    except Exception as e:
        print(f"❌ 發送 Power 封包失敗: {e}")

def ship_controller():
    pass

def push_video_process_func():
    sio = create_resilient_sio("Video")
    sio.emit("get_video_info", {"device": "edge_01", "url": RTSP_URL})
    retry_count = 0

    while True:
        if not os.path.exists(VIDEO_DEVICE):
            print(f"⚠️ Video device {VIDEO_DEVICE} not found. Retrying...")
            time.sleep(0.01)
            retry_count += 1
            if retry_count % 6 == 0:
                print(f"🔁 Retried {retry_count} times. Still waiting for video input...")
            continue

        retry_count = 0
        print(f"✅ Pushing video to {RTSP_URL}")

        cmd = [
            "ffmpeg",
            "-f", "v4l2",
            "-input_format", "yuyv422",              # ✅ 相機支援的格式（請勿用 nv12，除非明確支援）
            "-framerate", "25",                      # ✅ 穩定值，節省頻寬，減少卡頓
            "-video_size", "1280x720",               # ✅ 720p 足以辨識目標，也比 1080p 穩定

            "-i", VIDEO_DEVICE,

            "-c:v", "libx264",                       # ✅ 使用軟體編碼，穩定但吃 CPU
            "-pix_fmt", "yuv420p",                   # ✅ 相容大多數瀏覽器與播放端
            "-preset", "ultrafast",                  # ✅ 編碼延遲最低
            "-tune", "zerolatency",                  # ✅ 最佳化即時串流

            "-profile:v", "baseline",                # ✅ 增加與 WebRTC 瀏覽器相容性
            "-b:v", "1.5M",                          # ✅ 固定碼率，防突發頻寬問題
            "-maxrate", "1.5M",
            "-bufsize", "3M",
            "-g", "50",                              # ✅ 每兩秒一個 I-frame
            "-keyint_min", "50",                     # ✅ 配合 GOP 長度

            "-an",                                   # ✅ 無音訊
            "-f", "rtsp",
            "-rtsp_transport", "tcp",                # ✅ 行動網建議使用 TCP，較穩
            RTSP_URL
        ]



        try:
            process = subprocess.Popen(cmd)
            process.wait()
            print("❌ FFmpeg exited. Will retry in 5 seconds...")
        except Exception as e:
            print(f"❌ Video push error: {e}")

        time.sleep(5)

if __name__ == "__main__":
    try:
        load_config(path="config.yaml")
        multiprocessing.set_start_method("spawn")
        manager = Manager()
        share_imu = manager.dict(rpy=[0.0,0.0,0.0])
        share_gps = manager.dict(time="", latitude=0.0, longitude=0.0, altitude=0.0)
        imu_proc = Process(target=imu_process_func, args=(share_imu,))
        gps_proc = Process(target=gps_process_func, args=(share_gps,))
        controller_proc = Process(target=controller_process_func, args=(share_imu, share_gps,))
        # lidar_proc = Process(target=lidar_process_func)
        video_proc = Process(target=push_video_process_func)
        

        imu_proc.start()
        # lidar_proc.start()
        video_proc.start()
        gps_proc.start()
        controller_proc.start()

        imu_proc.join()
        # lidar_proc.join()
        video_proc.join()
        gps_proc.join()
        controller_proc.join()

    except KeyboardInterrupt:
        print("🛑 KeyboardInterrupt. Closing connection...")



#                _ooOoo_
#               o8888888o
#               88" . "88
#               (| -_- |)
#               O\  =  /O
#            ____/`---'\____
#          .'  \\|     |//  `.
#         /  \\|||  :  |||//  \
#        /  _||||| -:- |||||_  \
#        |   | \\\  -  /// |   |
#        | \_|  ''\---/''  |_/ |
#        \  .-\__  `-`  ___/-. /
#      ___`. .'  /--.--\  `. .'___
#   ."" '<  `.___\_<|>_/___.' _> \"".
#  | | :  `- \`.;`\ _ /`;.`/ - ` : | |
#  \  \ `-.   \_ __\ /__ _/   .-` /  /
# ======`-.____`-.___\_____/__.-`____.-'======
#                `=---='

