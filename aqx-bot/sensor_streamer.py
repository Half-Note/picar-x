import socket
import json
from picarx import Picarx
import time

UDP_IP = "192.168.1.102"  # Replace with your ROS 2 PC's IP address
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
px = Picarx()

def get_dummy_uwb_location():
    # Send fixed dummy UWB data
    return {'x': 1.23, 'y': 4.56, 'z': 0.78}

def get_dummy_imu_data():
    # Send fixed dummy IMU data
    return {
        "gyro": [0.0, 0.0, 0.0],
        "accel": [0.0, 0.0, 9.8],
        "mag": [0.1, 0.1, 0.1]
    }

while True:
    distance = px.ultrasonic.read() if hasattr(px, "ultrasonic") else -1.0
    uwb = get_dummy_uwb_location()
    imu_data = get_dummy_imu_data()

    data = {
        "ultrasonic_distance": distance,
        "uwb_location": uwb,
        "imu": imu_data
    }

    message = json.dumps(data).encode('utf-8')
    sock.sendto(message, (UDP_IP, UDP_PORT))
    time.sleep(0.1)  # Send at 10 Hz

