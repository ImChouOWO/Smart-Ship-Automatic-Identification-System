import subprocess
import socketio
import time
import threading
import serial
import os
from imu import DueData
import lidar

SERVER_URL = 'http://140.133.74.176:5000'
RTSP_URL = 'rtsp://140.133.74.176:8554/edge_cam'
VIDEO_DEVICE = '/dev/video0'

sio = socketio.Client()

@sio.event
def connect():
    print("\u2705 Connected to server")

@sio.event
def disconnect():
    print("\u274c Disconnected from server")

def lidar_callback(scan_results):
    lidar.PORT = '/dev/ttyUSB5'
    lidar.BAUDRATE = 1000000
    send_data = [{"angle": round(a, 2), "dist": round(d, 2), "q": q} for a, d, q in scan_results[:100]]
    sio.emit("get_lidar", send_data)
    print(f"\ud83d\udce4 Sent {len(send_data)} lidar points")

def lidar_thread_func():
    try:
        lidar.start_lidar_scan(callback=lidar_callback)
    except Exception as e:
        print(f"\u274c LiDAR thread error: {e}")

def imu_thread_func():
    port = '/dev/ttyUSB0'
    baud = 9600
    try:
        ser = serial.Serial(port, baud, timeout=0.5)
        print("\u2705 IMU Serial is Opened:", ser.is_open)
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
                print(f"\ud83d\udce4 Sent IMU data: {imu_data}")
                time.sleep(5)
    except Exception as e:
        print(f"\u274c IMU thread error: {e}")

def push_video_thread():
    sio.emit("get_video_info", {"device": "edge_01", "url": RTSP_URL})
    
    while True:
        if not os.path.exists(VIDEO_DEVICE):
            print(f"\u26a0\ufe0f Video device {VIDEO_DEVICE} not found. Retrying in 5 seconds...")
            time.sleep(5)
            continue

        print(f"\ud83d\ude80 Pushing video stream to {RTSP_URL}")

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
            process = subprocess.run(cmd)
            print("\u274c FFmpeg exited. Will retry in 5 seconds...")
        except Exception as e:
            print(f"\u274c Video push error: {e}")

        time.sleep(5)  # 等待再重新推流

if __name__ == "__main__":
    try:
        sio.connect(SERVER_URL)

        imu_thread = threading.Thread(target=imu_thread_func, daemon=True)
        lidar_thread = threading.Thread(target=lidar_thread_func, daemon=True)
        video_thread = threading.Thread(target=push_video_thread, daemon=True)

        imu_thread.start()
        # lidar_thread.start()
        video_thread.start()

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\ud83d\uded1 KeyboardInterrupt. Closing connection...")
        sio.disconnect()