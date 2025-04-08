import subprocess
import socketio
import time
import os
from imu import DueData
import lidar
from multiprocessing import Process
import multiprocessing
import serial

SERVER_URL = 'http://140.133.74.176:5000'
RTSP_URL = 'rtsp://140.133.74.176:8554/edge_cam'
VIDEO_DEVICE = '/dev/video0'
IMU = '/dev/imu'
LIDAR = '/dev/ttyUSB5'
GPS = "/dev/gps"

def create_resilient_sio(name="module"):
    while True:
        try:
            print(f"🔌 [{name}] Connecting to SocketIO server...")
            sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=3)

            @sio.event
            def connect():
                print(f"✅ [{name}] SocketIO Connected")

            @sio.event
            def disconnect():
                print(f"❌ [{name}] SocketIO Disconnected")

            sio.connect(SERVER_URL)
            return sio
        except Exception as e:
            print(f"❌ [{name}] SocketIO connection failed: {e}")
            time.sleep(3)

def lidar_callback(scan_results, sio):
    send_data = [{"angle": round(a, 2), "dist": round(d, 2), "q": q} for a, d, q in scan_results[:100]]
    if sio.connected:
        sio.emit("get_lidar", send_data)
        print(f"📤 Sent {len(send_data)} lidar points")
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
            time.sleep(3)

def imu_process_func():
    port = IMU
    baud = 9600
    sio = create_resilient_sio("IMU")

    try:
        ser = serial.Serial(port, baud, timeout=0.5)
        print("✅ IMU Serial Opened:", ser.is_open)
        time.sleep(1)

        while True:
            if not sio.connected:
                print("🔁 IMU SocketIO lost. Reconnecting...")
                sio = create_resilient_sio("IMU")

            RXdata = ser.read(1)
            if not RXdata:
                continue

            try:
                value = int(RXdata.hex(), 16)
            except ValueError:
                continue

            result = DueData(value)
            if result:
                imu_data = ['%.2f' % result[0], '%.2f' % result[1], '%.2f' % (result[2] - 167)]
                try:
                    if sio.connected:
                        sio.emit("get_imu", imu_data)
                        print(f"📤 Sent IMU data: {imu_data}")
                except Exception as e:
                    print(f"❌ IMU emit error: {e}")
                    time.sleep(1)

    except Exception as e:
        print(f"❌ IMU process fatal error: {e}")
        time.sleep(3)

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

def gps_process_func():
    port = GPS
    baud = 4800
    sio = create_resilient_sio("GPS")

    try:
        ser = serial.Serial(port, baud, timeout=0.5)
        print("✅ GPS Serial Opened:", ser.is_open)
        time.sleep(2)

        while True:
            if not sio.connected:
                print("🔁 GPS SocketIO lost. Reconnecting...")
                sio = create_resilient_sio("GPS")

            try:
                line = ser.readline().decode('ascii', errors='replace').strip()
                if line:
                    print(f"📥 NMEA: {line}")
                    time_str, lat, lon, alt = parse_nmea_gpgga(line)
                    if time_str and lat and lon:
                        
                        data = {
                            "time": time_str,
                            "latitude": lat,
                            "longitude": lon,
                            "altitude": alt
                        }
                        try:
                            if sio.connected:
                                sio.emit("get_gps", data)
                                print(f"📤 Sent GPS data: {data}")
                        except Exception as e:
                            print(f"❌ GPS emit error: {e}")
                        time.sleep(5)
                    else:
                        print("⚠️ GPGGA 無有效座標")
            except Exception as e:
                print(f"❌ GPS parse error: {e}")
                time.sleep(3)
    except Exception as e:
        print(f"❌ GPS Serial connect error: {e}")
        time.sleep(3)

def push_video_process_func():
    sio = create_resilient_sio("Video")
    sio.emit("get_video_info", {"device": "edge_01", "url": RTSP_URL})
    retry_count = 0

    while True:
        if not os.path.exists(VIDEO_DEVICE):
            print(f"⚠️ Video device {VIDEO_DEVICE} not found. Retrying...")
            time.sleep(5)
            retry_count += 1
            if retry_count % 6 == 0:
                print(f"🔁 Retried {retry_count} times. Still waiting for video input...")
            continue

        retry_count = 0
        print(f"✅ Pushing video to {RTSP_URL}")

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
        multiprocessing.set_start_method("spawn")
        imu_proc = Process(target=imu_process_func)
        lidar_proc = Process(target=lidar_process_func)
        video_proc = Process(target=push_video_process_func)
        gps_proc = Process(target=gps_process_func)

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
