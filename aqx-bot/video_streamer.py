# piw/video_streamer.py
import cv2
import socket
import struct
import pickle

server_ip = 'PI5_IP'
server_port = 8001

cap = cv2.VideoCapture(0)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((server_ip, server_port))
conn = sock.makefile('wb')

while True:
    ret, frame = cap.read()
    if not ret:
        continue
    data = pickle.dumps(frame)
    size = struct.pack('>L', len(data))
    conn.write(size + data)
