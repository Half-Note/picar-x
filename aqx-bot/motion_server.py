# piw/motion_server.py
import socket
import json
from picarx import Picarx
import time

px = Picarx()
HOST = '0.0.0.0'
PORT = 9000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen(1)
conn, addr = sock.accept()

def drive_linear_angular(linear, angular):
    px.set_dir_servo_angle(angular)
    if linear > 0:
        px.forward(linear)
    elif linear < 0:
        px.backward(-linear)
    else:
        px.stop()

try:
    while True:
        data = conn.recv(1024)
        if not data:
            break
        cmd = json.loads(data.decode())
        if "camera_angle" in cmd:
            px.set_camera_servo_angle(cmd["camera_angle"])
        if "linear" in cmd and "angular" in cmd:
            drive_linear_angular(cmd["linear"], cmd["angular"])
except Exception as e:
    print("Error:", e)
finally:
    px.stop()
    conn.close()
