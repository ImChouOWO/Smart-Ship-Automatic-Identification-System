import subprocess
from flask import Flask, render_template
from flask_socketio import SocketIO
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='*')  # 允許跨來源連接

# 儲存裝置資料
device_status = {}

@socketio.on('get_imu')
def get_imu(msg):
    print(f'Received message: {msg}')
    device_status.setdefault('edge_01', {})['imu'] = msg

@socketio.on("get_gps")
def get_gps(msg):
    print(f'Received message: {msg}')
    device_status.setdefault('edge_01', {})['gps'] = msg

@socketio.on("get_lidar")
def get_lidar(msg):
    print(f'Received message: {msg}')
    device_status.setdefault('edge_01', {})['lidar'] = f"{len(msg)} points"

@socketio.on("get_video_info")
def get_video_info(msg):
    device = msg.get("device", "unknown_device")
    stream_url = msg.get("url", "N/A")
    print(f'🎥 Received video stream info from {device}: {stream_url}')
    device_status.setdefault(device, {})['video_url'] = stream_url

@app.route('/')
def index():
    return '<h1>🚀 Socket.IO 測試伺服器</h1>'

@app.route('/status')
def status():
    html = "<h2>📡 Edge Devices 狀態</h2><ul>"
    for device, info in device_status.items():
        html += f"<li><strong>{device}</strong><ul>"
        if 'imu' in info:
            html += f"<li>IMU: {info['imu']}</li>"
        if 'gps' in info:
            html += f"<li>GPS: {info['gps']}</li>"
        if 'lidar' in info:
            html += f"<li>LiDAR: {info['lidar']}</li>"
        if 'video_url' in info:
            html += f"<li>RTSP: <a href='{info['video_url']}'>{info['video_url']}</a></li>"
        html += "</ul></li>"
    html += "</ul>"
    return html

# ✅ 在 Flask 啟動前先啟動 mediamtx
def start_rtsp_server():
    try:
        # 檢查是否已經有 mediamtx 執行中
        result = subprocess.run(["pgrep", "-f", "mediamtx"], capture_output=True, text=True)
        if result.stdout.strip() != "":
            print("⚠️ mediamtx 已在執行，略過啟動")
            return

        subprocess.Popen(["./mediamtx/mediamtx"])
        print("🎥 RTSP Server 啟動成功 ✅")
    except Exception as e:
        print(f"❌ 無法啟動 RTSP Server: {e}")
if __name__ == '__main__':
    start_rtsp_server()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
