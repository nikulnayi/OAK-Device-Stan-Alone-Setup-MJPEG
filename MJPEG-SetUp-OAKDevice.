import depthai as dai
import time
# Start defining a pipeline
pipeline = dai.Pipeline()

# Define a source - color camera
color_cam = pipeline.create(dai.node.ColorCamera)
color_cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
color_cam.initialControl.setManualFocus(100)  # 0..255

# Define left and right cameras for stereo vision
left = pipeline.create(dai.node.MonoCamera)
left.setBoardSocket(dai.CameraBoardSocket.CAM_B)  # Updated from LEFT to CAM_B
left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)

right = pipeline.create(dai.node.MonoCamera)
right.setBoardSocket(dai.CameraBoardSocket.CAM_C)  # Updated from RIGHT to CAM_C
right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)



# Create stereo depth node to compute depth map
stereo = pipeline.create(dai.node.StereoDepth)
stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
left.out.link(stereo.left)
right.out.link(stereo.right)

# # Create xout nodes for debugging (optional)
# xout_depth = pipeline.create(dai.node.XLinkOut)
# xout_depth.setStreamName("depth")
# stereo.depth.link(xout_depth.input)

# VideoEncoders for color camera and stereo depth
color_jpeg_enc = pipeline.create(dai.node.VideoEncoder)
color_jpeg_enc.setDefaultProfilePreset(30, dai.VideoEncoderProperties.Profile.MJPEG)
color_cam.video.link(color_jpeg_enc.input)

stereo_jpeg_enc = pipeline.create(dai.node.VideoEncoder)
stereo_jpeg_enc.setDefaultProfilePreset(30, dai.VideoEncoderProperties.Profile.MJPEG)
stereo.disparity.link(stereo_jpeg_enc.input)

# Script node
script = pipeline.create(dai.node.Script)
script.setProcessor(dai.ProcessorType.LEON_CSS)
color_jpeg_enc.bitstream.link(script.inputs['jpeg_color'])
stereo_jpeg_enc.bitstream.link(script.inputs['jpeg_stereo'])

script.setScript("""
    import socket
    import struct
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from socketserver import ThreadingMixIn

    class CamHTTPHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/normal':
                self.send_stream('jpeg_color')
            elif self.path == '/stereo':
                self.send_stream('jpeg_stereo')

        def send_stream(self, input_name):
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--frameBoundary')
            self.end_headers()
            while True:
                try:
                    frame = node.io[input_name].get()
                    self.wfile.write(b'--frameBoundary')
                    self.send_header('Content-type', 'image/jpeg')
                    self.send_header('Content-length', len(frame.getData()))
                    self.end_headers()
                    self.wfile.write(frame.getData())
                except Exception as e:
                    break

    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
         \"\"\"Handle requests in a separate thread.\"\"\"

    def run_server(server_class=ThreadedHTTPServer, handler_class=CamHTTPHandler, port=8080):
        server_address = ('', port)
        httpd = server_class(server_address, handler_class)
        httpd.serve_forever()

    run_server()
""")
# Connect the device and start the pipeline
# dai.DeviceInfo('10.36.115.61')
with dai.Device(pipeline) as device:
    # Device is now ready to use
    print("Device is running. Access the streams via HTTP at:")
    print("Normal view: http://<device-ip>:8080/normal")
    print("Stereo view: http://<device-ip>:8080/stereo")

    # Keep the script running
    try:
        while True:
            pass
    except KeyboardInterrupt:
        # Program was interrupted, stop the device
        pass

# device_object = dai.DeviceInfo("10.36.115.61")
# with dai.Device(pipeline, device_object) as device:
#         while not device.isClosed():
#             time.sleep(1)
