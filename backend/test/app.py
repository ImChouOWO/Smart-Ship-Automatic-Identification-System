from flask import Flask, render_template
from flask_socketio import SocketIO
from imu import DueData
from flask_cors import CORS
import serial
import time

app = Flask(__name__)
CORS(app)

# 啟用 CORS 支援
socketio = SocketIO(app, cors_allowed_origins="*")  # 設置允許所有來源的 CORS

# 模擬動態資料
dynamic_data = {"gyroscope_data": "initial_value"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
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

            # return [0, 0, 0]
            

if __name__ == '__main__':
    socketio.run(app, debug=True)



# 校正imu角度