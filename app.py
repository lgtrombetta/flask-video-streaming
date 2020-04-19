#!/usr/bin/env python
from importlib import import_module
import os
from flask import Flask, render_template, Response

import signal, sys
from shlex import split
from subprocess import Popen, PIPE, DEVNULL

# start gphoto2 and ffmpeg for the DSRL, handle SIGINT
def signal_handler(sig, frame):
	print('You pressed Ctrl+C!')
	print(pid)
	os.kill(pid, signal.SIGINT)
	sys.exit()


p1 = Popen(split("gphoto2 --stdout --capture-movie"), stdout=PIPE, stderr=DEVNULL)
p2 = Popen(split("ffmpeg -i - -vcodec rawvideo -pix_fmt yuv420p -threads 0 -f v4l2 /dev/video0"), stdin=p1.stdout, stdout=DEVNULL, stderr=DEVNULL)

global pid
pid = p1.pid

signal.signal(signal.SIGINT, signal_handler)


# import camera driver
if os.environ.get('CAMERA'):
    Camera = import_module('camera_' + os.environ['CAMERA']).Camera
else:
    from camera import Camera

# Raspberry Pi camera module (requires picamera package)
# from camera_pi import Camera

app = Flask(__name__)


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
