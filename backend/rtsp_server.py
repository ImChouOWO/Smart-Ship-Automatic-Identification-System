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
            "video/x-raw,width=1024,height=768,framerate=30/1 ! "
            "videoconvert ! x264enc tune=zerolatency bitrate=500 speed-preset=ultrafast ! "
            "rtph264pay config-interval=1 name=pay0 pt=96"
        )

    def do_create_element(self, url):
        print(f"📡 Launching RTSP pipeline for {self.launch_string}")
        return Gst.parse_launch(self.launch_string)

class RTSPServer:
    def __init__(self, port='8554', path='/video'):
        self.server = GstRtspServer.RTSPServer()
        self.server.set_service(port)

        factory = RTSPMediaFactory()
        factory.set_shared(True)

        mount_points = self.server.get_mount_points()
        mount_points.add_factory(path, factory)

        self.server.attach(None)
        print(f"🚀 RTSP Server started at rtsp://<Edge IP>:{port}{path}")

def main():
    server = RTSPServer()
    loop = GObject.MainLoop()
    loop.run()

if __name__ == '__main__':
    main()
