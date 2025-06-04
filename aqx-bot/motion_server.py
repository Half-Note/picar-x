#!/usr/bin/env python3
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')  # Force UTF-8

import socket
import struct
import signal
from picarx import Picarx
from time import sleep

px = Picarx()

# Last known angles
last_dir_angle = 0.0
last_camera_yaw = None
last_camera_pitch = None

def stop_all():
    print("Stopping robot and resetting all angles to zero...")
    px.stop()
    px.set_dir_servo_angle(0)
    px.set_cam_pan_angle(0)
    px.set_cam_tilt_angle(0)

def signal_handler(sig, frame):
    stop_all()
    print("\nProgram terminated via signal.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    global last_dir_angle, last_camera_yaw, last_camera_pitch

    UDP_PORT = 9001
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', UDP_PORT))
    sock.settimeout(1.0)

    print(f"Listening on UDP port {UDP_PORT}...")

    try:
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                data_len = len(data)

                if data_len == 8:
                    linear, angular = struct.unpack('ff', data)
                    camera_yaw = None
                    camera_pitch = None
                elif data_len == 12:
                    linear, angular, camera_yaw = struct.unpack('fff', data)
                    camera_pitch = None
                elif data_len == 16:
                    linear, angular, camera_yaw, camera_pitch = struct.unpack('ffff', data)
                else:
                    print(f"Unexpected packet size {data_len}, ignoring.")
                    continue

                print(f"Received: linear={linear:.2f}, angular={angular:.2f}, cam_yaw={camera_yaw}, cam_pitch={camera_pitch}")

                # Update steering servo always if angular changes
                new_dir_angle = max(min(angular * 10, 35), -35)
                if abs(new_dir_angle - last_dir_angle) > 0.1:
                    px.set_dir_servo_angle(new_dir_angle)
                    last_dir_angle = new_dir_angle

                # Linear motion
                if abs(linear) < 0.05:
                    px.stop()
                else:
                    if linear > 0:
                        px.forward(20)
                    elif linear < 0:
                        px.backward(20)

                # Camera pan
                if camera_yaw is not None:
                    yaw_clamped = max(min(camera_yaw, 35), -35)
                    if last_camera_yaw is None or abs(yaw_clamped - last_camera_yaw) >= 0.1:
                        px.set_cam_pan_angle(yaw_clamped)
                        last_camera_yaw = yaw_clamped

                # Camera tilt
                if camera_pitch is not None:
                    pitch_clamped = max(min(camera_pitch, 35), -35)
                    if last_camera_pitch is None or abs(pitch_clamped - last_camera_pitch) >= 0.1:
                        px.set_cam_tilt_angle(pitch_clamped)
                        last_camera_pitch = pitch_clamped

            except socket.timeout:
                print("Socket timeout: no data received, stopping motion only.")
                px.stop()
                # Steering/camera preserved

    except KeyboardInterrupt:
        print("KeyboardInterrupt detected.")

    finally:
        stop_all()
        print("Exiting safely.")

if __name__ == "__main__":
    main()

