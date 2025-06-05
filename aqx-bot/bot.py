#!/usr/bin/env python3
import subprocess
import time
import sys

SCRIPTS = [
    "/home/fahad/picar-x/aqx-bot/motion_server.py",
    "/home/fahad/picar-x/aqx-bot/video_streamer.py",
    "/home/fahad/picar-x/aqx-bot/sound.py"
]

def main():
    print("?? Starting PiCar-X services...")
    processes = []
    
    try:
        for script in SCRIPTS:
            cmd = ["sudo", "python3", script]
            p = subprocess.Popen(cmd)
            processes.append(p)
            print(f"? Launched: {' '.join(cmd)} (PID: {p.pid})")
            time.sleep(1)  # Prevent resource conflicts
            
        print("\n?? All services running! Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n?? Stopping all services...")
        for p in processes:
            p.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()