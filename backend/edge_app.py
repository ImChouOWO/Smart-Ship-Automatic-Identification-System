import socketio
import time
import threading
import serial
from imu import DueData
import lidar
import rtsp_server

# ✅ Socket.IO Server
SERVER_URL = 'http://140.133.74.176:5000'
sio = socketio.Client()

@sio.event
def connect():
    print("✅ Connected to server")

@sio.event
def disconnect():
    print("❌ Disconnected from server")

# ✅ LiDAR 執行緒：每圈掃描完就傳送資料
def lidar_callback(scan_results):
    lidar.PORT = '/dev/ttyUSB5'
    lidar.BAUDRATE = 1000000
    send_data = [{"angle": round(a, 2), "dist": round(d, 2), "q": q} for a, d, q in scan_results[:100]]  # 限制最多100筆
    sio.emit("get_lidar", send_data)
    print(f"📤 Sent {len(send_data)} lidar points")

def lidar_thread_func():
    try:
        lidar.start_lidar_scan(callback=lidar_callback)
    except Exception as e:
        print(f"❌ LiDAR thread error: {e}")

# ✅ IMU 執行緒：每隔幾秒讀一次發送
def imu_thread_func():
    port = '/dev/ttyUSB0'
    baud = 9600
    try:
        ser = serial.Serial(port, baud, timeout=0.5)
        print("✅ IMU Serial is Opened:", ser.is_open)
        time.sleep(1)  # 給 IMU 一點時間啟動

        while True:
            RXdata = ser.read(1)
            if not RXdata:
                continue  # 沒資料就跳過

            try:
                value = int(RXdata.hex(), 16)
            except ValueError:
                continue

            result = DueData(value)
            if result is not None:
                imu_data = [
                    '%.2f' % result[0],
                    '%.2f' % result[1],
                    '%.2f' % (result[2] - 167)
                ]
                sio.emit("get_imu", imu_data)
                print(f"📤 Sent IMU data: {imu_data}")
                time.sleep(5)
    except Exception as e:
        print(f"❌ IMU thread error: {e}")

# ✅ 主程式
if __name__ == "__main__":
    try:
        sio.connect(SERVER_URL)

        imu_thread = threading.Thread(target=imu_thread_func, daemon=True)
        lidar_thread = threading.Thread(target=lidar_thread_func, daemon=True)
        rtsp_thread = threading.Thread(target=rtsp_server.run_rtsp_server, daemon=True)
        imu_thread.start()
        # lidar_thread.start()

        # 主程式保持運作直到手動中斷
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("🛑 KeyboardInterrupt. Closing connection...")
        sio.disconnect()
