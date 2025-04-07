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
GPS ="ttyACM0"
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

        imu_proc.start()
        lidar_proc.start()
        video_proc.start()

        imu_proc.join()
        lidar_proc.join()
        video_proc.join()

    except KeyboardInterrupt:
        print("🛑 KeyboardInterrupt. Closing connection...")
