from picamera2 import Picamera2
import cv2
from flask import Flask, Response

app = Flask(__name__)

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))

# Set auto white balance to a warmer mode (like 'sunlight')
picam2.set_controls({"AwbMode": 2})  # 0=off, 1=auto, 2=sunlight, 3=cloudy, 4=shade, 5=tungsten, 6=fluorescent

picam2.start()

def generate_frames():
    while True:
        frame = picam2.capture_array()
        # Convert RGB (picamera2) to BGR (OpenCV) for correct colors
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        ret, jpeg = cv2.imencode('.jpg', frame_bgr)
        if not ret:
            continue
        frame_bytes = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("Open http://<your_pi_ip>:5000/video_feed")
    app.run(host='0.0.0.0', port=5000)
