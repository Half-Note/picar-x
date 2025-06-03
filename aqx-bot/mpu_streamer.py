# piw/mpu9250_streamer.py
import socket
import time
import json
from mpu9250_i2c import MPU9250  # Install MPU9250 Python library

sensor = MPU9250()
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('PI5_IP', 8002))

while True:
    data = {
        'accel': sensor.readAccel(),
        'gyro': sensor.readGyro(),
        'mag': sensor.readMagnet()
    }
    sock.sendall((json.dumps(data) + '\n').encode())
    time.sleep(0.05)
