# device_a_client.py
import socketio
import time
import random
import time

# 固定 IP server 的 IP，請替換成你的裝置 B IP
SERVER_URL = 'http://140.133.74.176:5000'  # 或公開 IP

sio = socketio.Client()

@sio.event
def connect():
    print("✅ Connected to server")

@sio.event
def disconnect():
    print("❌ Disconnected from server")


sio.connect(SERVER_URL)


if __name__ =="__main__":
    while True:
        try:
            data= "test imu data"
            sio.emit("get_imu",data)
            print(f"send:{data}")
            time.sleep(5)
        except KeyboardInterrupt:
            sio.disconnect()
