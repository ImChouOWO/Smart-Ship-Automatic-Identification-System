import subprocess
import socket
import time
import os
from flask import Flask
from flask_socketio import SocketIO
import cv2
import base64
import threading

RTSP_URL = 'rtsp://140.133.74.176:8554/edge_cam'
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')  # 允許跨來源連接
device_status = {}

def stream_rtsp_frames():
    cmd = [
        'ffmpeg',
        '-i', RTSP_URL,
        '-vf', 'scale=640:360',
        '-f', 'image2pipe',
        '-vcodec', 'mjpeg',
        '-'
    ]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    def read_jpeg():
        data = b''
        while True:
            byte = process.stdout.read(1)
            if not byte:
                return None
            data += byte
            if data.endswith(b'\xff\xd9'):  # JPEG 結尾標記
                return data

    print("📡 FFmpeg 啟動 RTSP → JPEG 串流中...")

    while True:
        try:
            jpeg = read_jpeg()
            if jpeg is None:
                break
            b64 = base64.b64encode(jpeg).decode('utf-8')
            socketio.emit('video_frame', b64)
            time.sleep(0.1)  # 控制幀率，10 fps
        except Exception as e:
            print(f"⚠️ FFmpeg 解碼錯誤: {e}")
            break


@socketio.on('get_imu')
def get_imu(msg):
    print(f'Received imu message: {msg}')
    device_status.setdefault('edge_01', {})['imu'] = msg
    msg ={
        "roll":msg[0],
        "pitch":msg[1],
        "yaw":msg[2],
    }
    socketio.emit("server_imu",msg)

@socketio.on("get_gps")
def get_gps(msg):
    
    """gps msg content
    data = {
            "time":time_str,
            "latitude":lat,
            "longitude":lon,
            "altitude":alt}       
    """
    print(f'Received gps message: {msg}')
    device_status.setdefault('edge_01', {})['gps'] = msg
    socketio.emit("server_gps",msg)

@socketio.on("get_lidar")
def get_lidar(msg):
    print(f'Received lidar message: {msg}')
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
            html += f"<li>RTSP: <a href='{info['video_url']}' target='_blank'>{info['video_url']}</a></li>"
        html += "</ul></li>"
    html += "</ul>"
    return html

# ✅ 檢查某個 port 是否打得開
def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

# ✅ 啟動 RTSP Server（mediamtx）
def start_rtsp_server():
    config_path = "./mediamtx/mediamtx.yml"
    executable = "./mediamtx/mediamtx"

    if not os.path.exists(config_path):
        print(f"❌ 找不到設定檔 {config_path}")
        return

    if not os.path.exists(executable):
        print(f"❌ 找不到 mediamtx 執行檔 {executable}")
        return

    # 是否已經啟動 mediamtx？
    result = subprocess.run(["pgrep", "-f", "mediamtx"], capture_output=True, text=True)
    if result.stdout.strip() != "":
        print("⚠️ mediamtx 已在執行，略過啟動")
        return

    print("🚀 啟動 mediamtx ...")
    subprocess.Popen([executable, config_path])

    # 等 port 開啟，最多等 10 秒
    for i in range(10):
        if is_port_open(8554):
            print("✅ RTSP Server 啟動成功 (port 8554)")
            return
        time.sleep(1)

    print("❌ RTSP Server 未能在 10 秒內啟動（port 8554 未開）")



if __name__ == '__main__':
    start_rtsp_server()
    threading.Thread(target=stream_rtsp_frames, daemon=True).start()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
