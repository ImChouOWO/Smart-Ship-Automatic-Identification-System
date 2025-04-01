# device_a_client.py
import socketio
import time
import threading
import serial
from imu import DueData
import lidar  # 導入你寫的 lidar.py 模組

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
    send_data = [{"angle": round(a, 2), "dist": round(d, 2), "q": q} for a, d, q in scan_results[:100]]  # 只取前100筆避免太大
    sio.emit("get_lidar", send_data)
    print(f"📤 Sent {len(send_data)} lidar points")

def lidar_thread_func():
    try:
        lidar.start_lidar_scan(callback=lidar_callback)
        time.sleep(5)
    except Exception as e:
        print(f"❌ LiDAR thread error: {e}")


# ✅ IMU 執行緒：每隔幾秒讀一次發送
def imu_thread_func():
    port = '/dev/ttyUSB4'
    imu_baud = 9600
    try:
        ser = serial.Serial(port, imu_baud, timeout=0.5)
        print("✅ IMU Serial is Opened:", ser.is_open)
        while True:
            RXdata = ser.read(1)
            RXdata = int(RXdata.hex(), 16)
            result = DueData(RXdata)
            if result is not None:
                imu_data = ['%.2f' % result[0], '%.2f' % result[1], '%.2f' % (result[2]-167)]
                sio.emit("get_imu", imu_data)
                print(f"📤 Sent IMU data: {imu_data}")
                time.sleep(5)
    except Exception as e:
        print(f"❌ IMU thread error: {e}")


# ✅ 主程式
if __name__ == "__main__":
    try:
        sio.connect(SERVER_URL)

        # 啟動 IMU 與 LiDAR 各自的執行緒
        imu_thread = threading.Thread(target=imu_thread_func, daemon=True)
        lidar_thread = threading.Thread(target=lidar_thread_func, daemon=True)

        imu_thread.start()
        # lidar_thread.start()

        # 主程式等待（可以改成 while True: sleep 也可以）
        imu_thread.join()
        # lidar_thread.join()

    except KeyboardInterrupt:
        print("🛑 KeyboardInterrupt. Closing connection...")
        sio.disconnect()
