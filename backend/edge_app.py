import subprocess
import socketio
import time
import os
from imu import DueData
import lidar
from multiprocessing import Process
import serial

SERVER_URL = 'http://140.133.74.176:5000'
RTSP_URL = 'rtsp://140.133.74.176:8554/edge_cam'
VIDEO_DEVICE = '/dev/video0'
IMU ='/dev/ttyUSB4'
LIDAR ='/dev/ttyUSB5'
GPS ="/dev/ttyACM0"
def create_sio():
    sio = socketio.Client()

    @sio.event
    def connect():
        print("✅ Connected to server")

    @sio.event
    def disconnect():
        print("❌ Disconnected from server")

    sio.connect(SERVER_URL)
    return sio

def lidar_callback(scan_results, sio):
    send_data = [{"angle": round(a, 2), "dist": round(d, 2), "q": q} for a, d, q in scan_results[:100]]
    sio.emit("get_lidar", send_data)
    print(f"📤 Sent {len(send_data)} lidar points")

def lidar_process_func():
    sio = create_sio()
    lidar.PORT = LIDAR
    lidar.BAUDRATE = 1000000
    try:
        lidar.start_lidar_scan(callback=lambda data: lidar_callback(data, sio))
    except Exception as e:
        print(f"❌ LiDAR process error: {e}")

def imu_process_func():
    sio = create_sio()
    port = IMU
    baud = 9600
    try:
        ser = serial.Serial(port, baud, timeout=0.5)
        print("✅ IMU Serial is Opened:", ser.is_open)
        time.sleep(1)
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
                imu_data = ['%.2f' % result[0], '%.2f' % result[1], '%.2f' % (result[2]-167)]
                sio.emit("get_imu", imu_data)
                print(f"📤 Sent IMU data: {imu_data}")
                time.sleep(5)
    except Exception as e:
        print(f"❌ IMU process error: {e}")

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

def gps_process_func():
    sio = create_sio()
    prot = GPS
    baud = 4800
    try:
        ser = serial.Serial(prot,baud, timeout=0.5)
        print("✅ GPS Serial is Opened:", ser.is_open)
        time.sleep(10)
        while True:
            try:
                line = ser.readline().decode('ascii', errors='replace').strip()
                if line:
                    # print(f"接收到的NMEA語句: {line}")
                    time_str, lat, lat_dir, lon, lon_dir, alt = parse_nmea_sentence(line)
                    if time_str and lat and lon:
                        print(f"時間: {time_str}")
                        print(f"緯度: {lat} {lat_dir}")
                        print(f"經度: {lon} {lon_dir}")
                        print(f"海拔: {alt} M")
                        data = {
                            "time":time_str,
                            "latitude":lat,
                            "longitude":lon,
                            "altitude":alt
                        }
                        sio.emit("get_gps",data)
                        print(f"📤 Sent IMU data: {data}")
                        time.sleep(5)
                    else:
                        print("NMEA data not avaliable...")
            except ValueError:
                print("無效的NMEA數據，繼續等待...")
                continue             
    except Exception as e:
        print(f'erro:{e}')



def push_video_process_func():
    sio = create_sio()
    sio.emit("get_video_info", {"device": "edge_01", "url": RTSP_URL})
    retry_count = 0
    while True:
        if not os.path.exists(VIDEO_DEVICE):
            print(f"⚠️ Video device {VIDEO_DEVICE} not found. Retrying in 5 seconds...")
            time.sleep(5)
            retry_count += 1
            if retry_count % 6 == 0:
                print(f"🔁 Retried {retry_count} times. Still waiting for video input...")
            continue

        retry_count = 0
        print(f"🚀 Pushing video stream to {RTSP_URL}")

        cmd = [
            "ffmpeg",
            "-re",
            "-f", "v4l2",
            "-framerate", "30",
            "-video_size", "1280x720",
            "-i", VIDEO_DEVICE,
            "-vcodec", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-an",
            "-f", "rtsp",
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
        imu_proc = Process(target=imu_process_func)
        lidar_proc = Process(target=lidar_process_func)
        video_proc = Process(target=push_video_process_func)
        gps_proc =Process(target=gps_process_func)

        imu_proc.start()
        lidar_proc.start()
        video_proc.start()
        gps_proc.start()

        imu_proc.join()
        lidar_proc.join()
        video_proc.join()
        gps_proc.join()

    except KeyboardInterrupt:
        print("🛑 KeyboardInterrupt. Closing connection...")
