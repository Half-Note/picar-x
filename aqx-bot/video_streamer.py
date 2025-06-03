#!/usr/bin/env python3

from robot_hat.utils import reset_mcu
from picarx import Picarx
from vilib import Vilib
from time import sleep, time, strftime, localtime
import readchar
import os
import socket
import cv2
import pickle
import struct

### EDIT THIS: IP address of Pi 5 ###
PI5_IP = '0.0.0.0'
PORT = 8001

user = os.getlogin()
user_home = os.path.expanduser(f'~{user}')

reset_mcu()
sleep(0.2)

manual = '''
Press key to call the function(non-case sensitive):

    O: speed up
    P: speed down
    W: forward  
    S: backward
    A: turn left
    D: turn right
    F: stop
    T: take photo

    Ctrl+C: quit
'''

px = Picarx()

def take_photo():
    _time = strftime('%Y-%m-%d-%H-%M-%S',localtime(time()))
    name = 'photo_%s' % _time
    path = f"{user_home}/Pictures/picar-x/"
    Vilib.take_photo(name, path)
    print(f'\nPhoto saved as {path}{name}.jpg')

def move(operate: str, speed):
    if operate == 'stop':
        px.stop()  
    else:
        if operate == 'forward':
            px.set_dir_servo_angle(0)
            px.forward(speed)
        elif operate == 'backward':
            px.set_dir_servo_angle(0)
            px.backward(speed)
        elif operate == 'turn left':
            px.set_dir_servo_angle(-30)
            px.forward(speed)
        elif operate == 'turn right':
            px.set_dir_servo_angle(30)
            px.forward(speed)

def init_video_socket(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, port))
        print("Connected to Pi 5 for video streaming.")
        return s
    except Exception as e:
        print(f"Video socket connection failed: {e}")
        return None

def send_frame(sock, frame):
    try:
        ret, jpeg = cv2.imencode('.jpg', frame)
        data = pickle.dumps(jpeg)
        sock.sendall(struct.pack('>L', len(data)) + data)
    except Exception as e:
        print(f"Send frame failed: {e}")

def main():
    speed = 0
    status = 'stop'

    Vilib.camera_start(vflip=False, hflip=False)
    Vilib.display(local=True, web=False)
    sleep(2)

    video_sock = init_video_socket(PI5_IP, PORT)
    print(manual)

    while True:
        print("\rstatus: %s , speed: %s    " % (status, speed), end='', flush=True)

        frame = Vilib.frame  # Grab current frame
        if frame is not None and video_sock:
            send_frame(video_sock, frame)

        key = readchar.readkey().lower()

        if key in ('wsadfop'):
            if key == 'o':
                if speed <= 90:
                    speed += 10           
            elif key == 'p':
                if speed >= 10:
                    speed -= 10
                if speed == 0:
                    status = 'stop'
            elif key in ('wsad'):
                if speed == 0:
                    speed = 10
                if key == 'w':
                    if status != 'forward' and speed > 60:
                        speed = 60
                    status = 'forward'
                elif key == 'a':
                    status = 'turn left'
                elif key == 's':
                    if status != 'backward' and speed > 60:
                        speed = 60
                    status = 'backward'
                elif key == 'd':
                    status = 'turn right' 
            elif key == 'f':
                status = 'stop'
            move(status, speed)  

        elif key == 't':
            take_photo()
        elif key == readchar.key.CTRL_C:
            print('\nquit ...')
            px.stop()
            Vilib.camera_close()
            break 

        sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:    
        print(f"error: {e}")
    finally:
        px.stop()
        Vilib.camera_close()
