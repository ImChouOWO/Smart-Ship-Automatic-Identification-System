# ais backendfrom flask import Flask, render_template
from flask_socketio import SocketIO, send
from flask import Flask, render_template
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
socketio = SocketIO(app, cors_allowed_origins='*')  # 允許跨來源連接


@socketio.on('get_imu')
def get_imu(msg):
    print(f'Received message: {msg}')

@socketio.on("get_gps")
def get_gps(msg):
    print(f'Received message: {msg}')

@socketio.on("get_lidar")
def get_lidar(msg):
    print(f'Received message: {msg}')

@socketio.on("get_video_info")
def get_video_info(msg):
    device = msg.get("device", "unknown_device")
    stream_url = msg.get("url", "N/A")
    print(f'🎥 Received video stream info from {device}: {stream_url}')

@app.route('/')
def index():
    return '<h1>🚀 Socket.IO 測試伺服器</h1>'

device_status = {}
@app.route('/status')
def status():
    html = "<h2>📡 Edge Devices's 狀態</h2><ul>"
    for device, info in device_status.items():
        html += f"<li><strong>{device}</strong><ul>"
        if 'imu' in info:
            html += f"<li>IMU: {info['imu']}</li>"
        if 'lidar' in info:
            html += f"<li>LiDAR: {info['lidar']}</li>"
        if 'video_url' in info:
            html += f"<li>RTSP: <a href='{info['video_url']}'>{info['video_url']}</a></li>"
        html += "</ul></li>"
    html += "</ul>"
    
    return html

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)