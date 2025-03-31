# device_a_client.py
import socketio
import time
import random
import time
from imu import DueData
import serial

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


def get_imu_data():
    port = '/dev/ttyUSB0' # USB serial port linux
    baud = 9600   # Same baud rate as the INERTIAL navigation module
    ser = serial.Serial(port, baud, timeout=0.5)
    print("Serial is Opened:", ser.is_open)
    while(1):
        RXdata = ser.read(1)#一个一个读
        RXdata = int(RXdata.hex(),16) #转成16进制显示
        result = DueData(RXdata)
        if result != None:
            # print(result)
            time.sleep(0.2)
            print(type(result[2]))
            return ['%.2f' % result[0], '%.2f' % result[1], '%.2f' % (result[2]-167)]
        
        return "No imu info"

if __name__ =="__main__":
    while True:
        try:
            data= get_imu_data()
            sio.emit("get_imu",data)
            print(f"send:{data}")
            time.sleep(5)
        except KeyboardInterrupt:
            sio.disconnect()
