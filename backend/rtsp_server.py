#!/usr/bin/env python3
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')

from gi.repository import Gst, GstRtspServer, GObject

Gst.init(None)

class RTSPMediaFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, device='/dev/video0'):
        super(RTSPMediaFactory, self).__init__()
        self.launch_string = (
            f"v4l2src device={device} ! "
            "video/x-raw,width=640,height=480,framerate=30/1 ! "
            "videoconvert ! x264enc tune=zerolatency bitrate=500 speed-preset=ultrafast ! "
            "rtph264pay config-interval=1 name=pay0 pt=96"
        )

    def do_create_element(self, url):
        return Gst.parse_launch(self.launch_string)

class RTSPServer:
    def __init__(self, port='8554'):
        self.server = GstRtspServer.RTSPServer()
        self.server.set_service(port)

        factory = RTSPMediaFactory(device='/dev/video0')  # 擷取卡位置
        factory.set_shared(True)

        mount_points = self.server.get_mount_points()
        mount_points.add_factory("/video", factory)

        self.server.attach(None)
        print(f"🚀 RTSP Stream ready at rtsp://localhost:{port}/video")

def run_rtsp_server():
    server = RTSPServer()
    loop = GObject.MainLoop()
    loop.run()
