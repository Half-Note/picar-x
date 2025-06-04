from vilib import Vilib
from time import sleep

def main():
    Vilib.camera_start()
    Vilib.display()  # This enables the web stream
    print("Camera stream started. Access it via http://<Pi-IP>:9000/mjpg")
    while True:
        sleep(1)  # Just keep the program alive

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
