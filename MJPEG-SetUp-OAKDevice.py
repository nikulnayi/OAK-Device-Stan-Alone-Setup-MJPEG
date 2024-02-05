import depthai as dai

# Create pipeline
pipeline = dai.Pipeline()

# Define sources - color camera and mono cameras
colorCam = pipeline.create(dai.node.ColorCamera)
colorCam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)

monoLeft = pipeline.create(dai.node.MonoCamera)
monoRight = pipeline.create(dai.node.MonoCamera)
monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
monoLeft.setBoardSocket(dai.CameraBoardSocket.CAM_B)
monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
monoRight.setBoardSocket(dai.CameraBoardSocket.CAM_C)

# Create output for color camera
xoutColor = pipeline.create(dai.node.XLinkOut)
xoutColor.setStreamName("color")
colorCam.video.link(xoutColor.input)

# Set up stereo depth
depth = pipeline.create(dai.node.StereoDepth)
depth.setExtendedDisparity(False)
depth.setSubpixel(False)
depth.setLeftRightCheck(True)
depth.initialConfig.setConfidenceThreshold(200)
depth.setDepthAlign(dai.CameraBoardSocket.CAM_A)
monoLeft.out.link(depth.left)
monoRight.out.link(depth.right)

# Create output for depth
xoutDepth = pipeline.create(dai.node.XLinkOut)
xoutDepth.setStreamName("depth")
depth.disparity.link(xoutDepth.input)

# Script node
script = pipeline.create(dai.node.Script)
script.inputs['color'].setBlocking(False)
script.inputs['color'].setQueueSize(1)
script.inputs['depth'].setBlocking(False)
script.inputs['depth'].setQueueSize(1)
colorCam.video.link(script.inputs['color'])
depth.disparity.link(script.inputs['depth'])

script.setScript("""
import socket
import struct
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import cv2
import numpy as np

class CamHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/normal':
            self.send_stream('color')
        elif self.path == '/stereo':
            self.send_stream('depth')
        else:
            self.send_error(404, "Page Not Found")

    def send_stream(self, input_name):
        self.send_response(200)
        self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--frameBoundary')
        self.end_headers()
        while True:
            data = node.io[input_name].tryGet()
            if data is not None:
                frame = data.getCvFrame()
                if input_name == 'depth':
                    # Normalize and colorize depth frame for visualization
                    frame = (frame * (255 / node.getMaxDisparity())).astype(np.uint8)
                    frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)
                _, encodedImage = cv2.imencode('.jpg', frame)
                self.wfile.write(b'--frameBoundary\\r\\n')
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Content-length', len(encodedImage))
                self.end_headers()
                self.wfile.write(bytearray(encodedImage))
                self.wfile.write(b'\\r\\n')

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    # Handle requests in a separate thread

def run_server():
    server_address = ('', 8080)
    httpd = ThreadedHTTPServer(server_address, CamHTTPHandler)
    httpd.serve_forever()

run_server()
""")


# Connect device and start pipeline
with dai.Device(pipeline) as device:
    # Device is now ready to start the pipeline
    while True:
        pass  # Keep the script running

