import subprocess
import socketio
import time
import os
from imu import DueData
import lidar
from multiprocessing import Process
import serial
import fcntl
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



USBDEVFS_RESET = 21780

def reset_usb(dev_bus_device_path):
    try:
        with open(dev_bus_device_path, 'w') as f:
            fcntl.ioctl(f, USBDEVFS_RESET, 0)
        print(f"🔌 成功重啟 USB 裝置: {dev_bus_device_path}")
        return True
    except Exception as e:
        print(f"❌ USB 裝置重啟失敗: {e}")
        return False

def get_usb_bus_device_path(dev_node="/dev/ttyACM0"):
    try:
        output = subprocess.check_output(f"udevadm info -q path -n {dev_node}", shell=True).decode().strip()
        usb_path = f"/sys{output}"
        for root, dirs, files in os.walk(usb_path):
            if "busnum" in files and "devnum" in files:
                with open(os.path.join(root, "busnum")) as f:
                    bus = int(f.read().strip())
                with open(os.path.join(root, "devnum")) as f:
                    dev = int(f.read().strip())
                return f"/dev/bus/usb/{bus:03d}/{dev:03d}"
    except Exception as e:
        print(f"❌ 找不到 USB 路徑: {e}")
    return None

def reset_gps_usb(dev_node="/dev/ttyACM0"):
    path = get_usb_bus_device_path(dev_node)
    if path:
        return reset_usb(path)
    else:
        print("⚠️ 無法取得 GPS 裝置的 bus/device 路徑")
        return False

def gps_process_func():
    sio = create_sio()
    prot = GPS
    baud = 4800
    invalid_nmea_count = 0
    MAX_INVALID_COUNT = 10

    try:
        ser = serial.Serial(prot, baud, timeout=0.5)
        print("✅ GPS Serial is Opened:", ser.is_open)
        time.sleep(10)

        while True:
            try:
                line = ser.readline().decode('ascii', errors='replace').strip()
                if line:
                    print(f"📥 接收到的NMEA語句: {line}")
                    time_str, lat, lat_dir, lon, lon_dir, alt = parse_nmea_sentence(line)
                    if time_str and lat and lon:
                        data = {
                            "time": time_str,
                            "latitude": lat,
                            "longitude": lon,
                            "altitude": alt
                        }
                        sio.emit("get_gps", data)
                        print(f"📤 Sent GPS data: {data}")
                        invalid_nmea_count = 0  # 重置錯誤計數器
                        time.sleep(5)
                    else:
                        invalid_nmea_count += 1
                        print(f"⚠️ 無效的NMEA數據（第 {invalid_nmea_count} 次）")
                        if invalid_nmea_count >= MAX_INVALID_COUNT:
                            print("🧯 嘗試自動重啟 GPS 裝置...")
                            ser.close()
                            if reset_gps_usb(prot):
                                time.sleep(3)
                                ser = serial.Serial(prot, baud, timeout=0.5)
                                print("🔁 GPS 裝置重新連線完成")
                            else:
                                print("🚫 GPS 裝置重啟失敗，跳過重啟")
                            invalid_nmea_count = 0
                        time.sleep(5)
            except Exception as e:
                print(f"❌ 讀取錯誤: {e}")
                time.sleep(5)
    except Exception as e:
        print(f'❌ GPS 初始化錯誤: {e}')




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
