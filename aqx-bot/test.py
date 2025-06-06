#!/usr/bin/env python3
import sys
import io
import struct
import signal
import socket
import json
import threading
from time import sleep, time
from picarx import Picarx
from robot_hat import Music, TTS

# Force UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Constants
SAFE_DISTANCE = 40   # cm
DANGER_DISTANCE = 20 # cm
ROS2_UDP_IP = "192.168.1.102"  # Replace with your ROS 2 PC's IP
ROS2_UDP_PORT = 5005
CONTROL_PORT = 9001
SOUND_PORT = 9100
CONTROL_TIMEOUT = 0.1  # Reduced timeout for more responsive control

# Initialize modules
px = Picarx()
music = Music()
tts = TTS()
tts.lang("en-US")

# State
last_dir_angle = 0.0
last_camera_yaw = None
last_camera_pitch = None
stop_flag = threading.Event()

# Sound system functions
def play_horn():
    print("\U0001F514 Honking...")
    music.sound_play_threading('../sounds/car-double-horn.wav')

def speak(text):
    print(f"\U0001F5E3 TTS: {text}")
    tts.say(text)

def sound_system_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', SOUND_PORT))
    sock.settimeout(0.1)  # Shorter timeout for better responsiveness
    print(f"\U0001F50E Sound system listening on UDP port {SOUND_PORT}...")

    while not stop_flag.is_set():
        try:
            data, _ = sock.recvfrom(1024)
            msg = data.decode().strip()
            if msg.startswith("SAY:"):
                speak(msg.split(":", 1)[1])
            elif msg == "HORN":
                play_horn()
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Sound system error: {e}")
    sock.close()

# Obstacle detection with horn
def obstacle_detection():
    while not stop_flag.is_set():
        try:
            distance = round(px.ultrasonic.read(), 2)
            print("?? Distance:", distance, "cm")

            if distance < DANGER_DISTANCE:
                play_horn()
                sleep(1)  # Prevent continuous honking
            sleep(0.1)
        except Exception as e:
            print(f"Obstacle detection error: {e}")
            sleep(1)

# Dummy data helpers
def get_dummy_uwb():
    return {'x': 1.23, 'y': 4.56, 'z': 0.78}

def get_dummy_imu():
    return {
        "gyro": [0.0, 0.0, 0.0],
        "accel": [0.0, 0.0, 9.8],
        "mag": [0.1, 0.1, 0.1]
    }

# Sensor UDP streaming
def sensor_stream():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while not stop_flag.is_set():
        try:
            dist = px.ultrasonic.read() if hasattr(px, "ultrasonic") else -1.0
            data = {
                "ultrasonic_distance": dist,
                "uwb_location": get_dummy_uwb(),
                "imu": get_dummy_imu()
            }
            msg = json.dumps(data).encode('utf-8')
            sock.sendto(msg, (ROS2_UDP_IP, ROS2_UDP_PORT))
            sleep(0.1)
        except Exception as e:
            print(f"Sensor stream error: {e}")
            sleep(1)
    sock.close()

# Improved non-blocking motion control listener
def control_listener():
    global last_dir_angle, last_camera_yaw, last_camera_pitch
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', CONTROL_PORT))
    sock.settimeout(CONTROL_TIMEOUT)
    print(f"Listening for motion/camera commands on UDP port {CONTROL_PORT}...")

    while not stop_flag.is_set():
        try:
            data, _ = sock.recvfrom(1024)
            if len(data) not in [8, 12, 16]:
                print(f"Unexpected packet size: {len(data)}")
                continue

            linear, angular, *camera = struct.unpack('f' * (len(data) // 4), data)
            yaw, pitch = (camera + [None, None])[:2]
            
            # Only print if we have meaningful values
            if abs(linear) > 0.01 or abs(angular) > 0.01 or (yaw is not None and abs(yaw) > 0.1) or (pitch is not None and abs(pitch) > 0.1):
                print(f"Cmd: linear={linear:.2f}, angular={angular:.2f}, yaw={yaw}, pitch={pitch}")

            # Steering
            new_dir = max(min(angular * 10, 35), -35)
            if abs(new_dir - last_dir_angle) > 0.1:
                px.set_dir_servo_angle(new_dir)
                last_dir_angle = new_dir

            # Driving - only act if above threshold
            if abs(linear) < 0.05:
                px.stop()
            else:
                px.forward(20) if linear > 0 else px.backward(20)

            # Camera pan/tilt
            if yaw is not None:
                yaw = max(min(yaw, 35), -35)
                if last_camera_yaw is None or abs(yaw - last_camera_yaw) > 0.1:
                    px.set_cam_pan_angle(yaw)
                    last_camera_yaw = yaw

            if pitch is not None:
                pitch = max(min(pitch, 35), -35)
                if last_camera_pitch is None or abs(pitch - last_camera_pitch) > 0.1:
                    px.set_cam_tilt_angle(pitch)
                    last_camera_pitch = pitch

        except socket.timeout:
            continue
        except Exception as e:
            print(f"Control listener error: {e}")
            sleep(1)
    sock.close()
    px.stop()  # Ensure robot stops when control listener exits

# Safe shutdown
def stop_all():
    print("\nStopping all systems...")
    stop_flag.set()
    px.stop()
    px.set_dir_servo_angle(0)
    px.set_cam_pan_angle(0)
    px.set_cam_tilt_angle(0)

def signal_handler(sig, frame):
    stop_all()
    print("Terminated by signal.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Main
def main():
    # Start all threads
    threads = [
        threading.Thread(target=sensor_stream, daemon=True),
        threading.Thread(target=sound_system_listener, daemon=True),
        threading.Thread(target=obstacle_detection, daemon=True),
        threading.Thread(target=control_listener, daemon=True)
    ]

    for t in threads:
        t.start()

    # Keep main thread alive
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        stop_all()

if __name__ == '__main__':
    main()