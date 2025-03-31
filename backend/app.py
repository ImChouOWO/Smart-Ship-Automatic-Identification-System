# ais backendfrom flask import Flask, render_template
from flask_socketio import SocketIO, send
from flask import Flask, render_template
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)



@socketio.on('get_imu')
def get_imu(msg):
    print(f'Received message: {msg}')

@socketio.on("get_gps")
def get_gps(msg):
    print(f'Received message: {msg}')

@socketio.on("get_lidar")
def get_lidar(msg):
    print(f'Received message: {msg}')
   

if __name__ == '__main__':
    socketio.run(app, debug=True)
