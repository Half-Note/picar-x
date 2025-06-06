#!/usr/bin/env python3
from time import sleep
from picarx import Picarx
from robot_hat import Music, TTS
import socket
import threading
import signal
import sys

# Constants
SafeDistance = 40   # cm
DangerDistance = 20 # cm

# Initialize
px = Picarx()
music = Music()
tts = TTS()
tts.lang("en-US")

# Play horn sound
def play_horn():
    print('?? Obstacle too close! Honking...')
    music.sound_play_threading('../sounds/car-double-horn.wav')

# Speak text
def speak(text):
    print(f'?? TTS: {text}')
    tts.say(text)

# Clean shutdown
def stop_all():
    print("?? Sound system shutting down.")

def signal_handler(sig, frame):
    stop_all()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# UDP listener for TTS
def socket_listener():
    UDP_PORT = 9100
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', UDP_PORT))
    sock.settimeout(0.5)
    print(f"?? Listening on UDP port {UDP_PORT} for TTS and horn...")

    while True:
        try:
            data, _ = sock.recvfrom(1024)
            msg = data.decode().strip()
            if msg.startswith("SAY:"):
                sentence = msg.split(":", 1)[1]
                speak(sentence)
            elif msg == "HORN":
                play_horn()
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Socket error: {e}")

# Start socket listener
threading.Thread(target=socket_listener, daemon=True).start()

# Main loop just for horn logic
def main():
    while True:
        distance = round(px.ultrasonic.read(), 2)
        print("?? Distance:", distance, "cm")

        if distance < DangerDistance:
            play_horn()
            sleep(1)
        else:
            sleep(0.2)

if __name__ == '__main__':
    main()
