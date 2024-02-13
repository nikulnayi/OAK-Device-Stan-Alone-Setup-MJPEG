import depthai as dai
import time

# Start defining a pipeline
pipeline = dai.Pipeline()
# Define a source - color camera
cam = pipeline.create(dai.node.ColorCamera)
cam.setFps(60)
cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
cam.initialControl.setManualFocus(185) # 0..255

manip = pipeline.create(dai.node.ImageManip)# Calculate the normalized crop rectangle for a 960x540 crop
manip.initialConfig.setCropRect(0.3917, 0.3574, 0.6083, 0.7426)

# VideoEncoder
jpeg = pipeline.create(dai.node.VideoEncoder)
jpeg.setDefaultProfilePreset(cam.getFps(), dai.VideoEncoderProperties.Profile.MJPEG)
jpeg.setQuality(50)
# Script node
script = pipeline.create(dai.node.Script)

script.setProcessor(dai.ProcessorType.LEON_CSS)
script.setScript("""
    import time
    import socket
    import fcntl
    import struct
    from socketserver import ThreadingMixIn
    from http.server import BaseHTTPRequestHandler, HTTPServer

    PORT = 8080

    def get_ip_address(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            -1071617759,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15].encode())
        )[20:24])

    class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
        pass

    class HTTPHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'<h1>[DepthAI] Hello, world!</h1><p>Click <a href="img">here</a> for an image</p>')
            elif self.path == '/img':
                try:
                    self.send_response(200)
                    self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
                    self.end_headers()
                    fpsCounter = 0
                    timeCounter = time.time()
                    while True:
                        jpegImage = node.io['jpeg'].get()
                        self.wfile.write("--jpgboundary".encode())
                        self.wfile.write(bytes([13, 10]))
                        self.send_header('Content-type', 'image/jpeg')
                        self.send_header('Content-length', str(len(jpegImage.getData())))
                        self.end_headers()
                        self.wfile.write(jpegImage.getData())
                        self.end_headers()

                        fpsCounter = fpsCounter + 1
                        if time.time() - timeCounter > 1:
                            node.warn(f'FPS: {fpsCounter}')
                            fpsCounter = 0
                            timeCounter = time.time()
                except Exception as ex:
                    node.warn(str(ex))

    with ThreadingSimpleServer(("", PORT), HTTPHandler) as httpd:
        node.warn(f"Serving at {get_ip_address('re0')}:{PORT}")
        httpd.serve_forever()
""")

# Connections
# Linking
cam.video.link(manip.inputImage)  # Link camera to ImageManip
manip.out.link(jpeg.input)  # Link ImageManip to VideoEncoder
jpeg.bitstream.link(script.inputs['jpeg'])

# device_info = dai.DeviceInfo("0.0.0.0")
# if device_info:
#     try:
#         print(device_info)
#         progress = lambda p: print(f'Flashing progress: {p*100:.1f}%') 
#         # Start the flashing process
#         dai.DeviceBootloader(devInfo=device_info).flash(progress, pipeline) 
#         print("Flashing completed.")
#     except Exception as e:
#         # Handle exceptions that occurred during the flashing process
#         print(f"An error occurred during flashing: {e}")
# else:
#     print(f"No device with IP address {device_info.name} found.")


device_info = dai.DeviceInfo("0.0.0.0") # Device IP Address
with dai.Device(pipeline, device_info) as device:
    while not device.isClosed():
        time.sleep(1)
