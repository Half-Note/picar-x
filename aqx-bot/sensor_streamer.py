import socket
import json
from picarx import Picarx
import time

UDP_IP = "192.168.192.128"  # Replace with your ROS2 PC IP address
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
px = Picarx()

def get_uwb_location():
    # Replace with actual UWB reading code
    return {'x': 1.23, 'y': 4.56, 'z': 0.78}

while True:
    distance = px.ultrasonic.read()
    imu = px.imu
    uwb = get_uwb_location()

    data = {
        "ultrasonic_distance": distance,
        "uwb_location": uwb,
        "imu": {
            "gyro": imu.gyro,      # list of 3 floats
            "accel": imu.accel,    # list of 3 floats
            "mag": imu.mag         # list of 3 floats
        }
    }

    message = json.dumps(data).encode('utf-8')
    sock.sendto(message, (UDP_IP, UDP_PORT))
    time.sleep(0.1)  # 10 Hz
