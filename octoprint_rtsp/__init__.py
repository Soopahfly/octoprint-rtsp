# -*- coding: utf-8 -*-
from __future__ import absolute_import

import threading
import time
import octoprint.plugin
import flask
import urllib.request
import urllib.error
import tornado.web
import tornado.gen
from .streamor import Streamor

# Global reference to plugin instance for Tornado handler
_plugin_instance = None


class MjpegStreamHandler(tornado.web.RequestHandler):
    """Native Tornado handler for MJPEG streaming - bypasses Flask/WSGI buffering"""

    def initialize(self):
        self._closed = False

    def on_connection_close(self):
        self._closed = True
        if _plugin_instance:
            _plugin_instance._logger.info("Stream client disconnected")

    @tornado.gen.coroutine
    def get(self):
        global _plugin_instance
        if not _plugin_instance:
            self.set_status(500)
            self.finish("Plugin not initialized")
            return

        plugin = _plugin_instance
        plugin._logger.info("Tornado stream request received!")

        rtsp_url = plugin._settings.get(["rtsp_url"])
        if not rtsp_url:
            self.set_status(400)
            self.finish("RTSP URL not configured")
            return

        # Ensure streamor is running
        with plugin._streamor_lock:
            if not plugin._streamor:
                plugin.on_settings_save({})
            if plugin._streamor and not plugin._streamor.running:
                plugin._streamor.start()

        if not plugin._streamor:
            self.set_status(500)
            self.finish("Streamor not available")
            return

        # Wait for first frame
        first_frame = None
        for _ in range(50):  # Wait up to 5 seconds
            first_frame = plugin._streamor.get_snapshot()
            if first_frame:
                break
            yield tornado.gen.sleep(0.1)

        if not first_frame:
            self.set_status(503)
            self.finish("No frames available")
            return

        # Set headers for MJPEG stream
        self.set_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.set_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "0")
        self.set_header("Connection", "close")

        plugin._logger.info(f"Streaming first frame: {len(first_frame)} bytes")

        # Send first frame
        try:
            self.write(b"--frame\r\n")
            self.write(b"Content-Type: image/jpeg\r\n")
            self.write(f"Content-Length: {len(first_frame)}\r\n\r\n".encode())
            self.write(first_frame)
            self.write(b"\r\n")
            yield self.flush()
        except Exception as e:
            plugin._logger.error(f"Error sending first frame: {e}")
            return

        # Stream continuously
        frame_count = 1
        streamor = plugin._streamor

        while not self._closed and streamor and streamor.running:
            # Get frame (with brief wait)
            frame = None
            with streamor._condition:
                streamor._condition.wait(timeout=0.5)
                frame = streamor.last_frame

            if frame and not self._closed:
                frame_count += 1
                if frame_count % 30 == 0:  # Log every ~2 seconds
                    plugin._logger.info(f"Streamed {frame_count} frames")

                try:
                    self.write(b"--frame\r\n")
                    self.write(b"Content-Type: image/jpeg\r\n")
                    self.write(f"Content-Length: {len(frame)}\r\n\r\n".encode())
                    self.write(frame)
                    self.write(b"\r\n")
                    yield self.flush()
                except tornado.iostream.StreamClosedError:
                    plugin._logger.info("Stream closed by client")
                    break
                except Exception as e:
                    plugin._logger.error(f"Error streaming frame: {e}")
                    break

        plugin._logger.info(f"Stream ended after {frame_count} frames")


class RtspPlugin(octoprint.plugin.StartupPlugin,
                 octoprint.plugin.SettingsPlugin,
                 octoprint.plugin.AssetPlugin,
                 octoprint.plugin.TemplatePlugin,
                 octoprint.plugin.BlueprintPlugin,
                 octoprint.plugin.SoftwareUpdatePlugin):

    def __init__(self):
        self._streamor = None
        self._streamor_lock = threading.Lock()

    def on_after_startup(self):
        global _plugin_instance
        _plugin_instance = self
        self._logger.info("OctoPrint-RTSP loaded!")
        # Load settings and init streamor
        self.on_settings_save({})

    def get_settings_defaults(self):
        return dict(
            rtsp_url="",
            username="",
            password="",
            # Streaming
            stream_fps=15,
            stream_resolution="", # e.g. 640x480
            stream_bitrate="",    # e.g. 1000k
            ffmpeg_custom_args="",
            # Orientation
            flip_h=False,
            flip_v=False,
            rotate_90=False,
            # PTZ
            use_ptz=False,
            ptz_url_left="",
            ptz_url_right="",
            ptz_url_up="",
            ptz_url_down="",
            ptz_url_zoom_in="",
            ptz_url_zoom_out="",
            ptz_url_home=""
        )

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

        rtsp_url = self._settings.get(["rtsp_url"])
        flip_h = self._settings.get_boolean(["flip_h"])
        flip_v = self._settings.get_boolean(["flip_v"])
        rotate_90 = self._settings.get_boolean(["rotate_90"])

        # Advanced
        resolution = self._settings.get(["stream_resolution"])
        current_fps = self._settings.get_int(["stream_fps"])
        bitrate = self._settings.get(["stream_bitrate"])
        custom_args = self._settings.get(["ffmpeg_custom_args"])

        if self._streamor:
            self._streamor.stop()

        # Initialize new streamor with new settings
        self._streamor = Streamor(
            url=rtsp_url,
            flip_h=flip_h,
            flip_v=flip_v,
            rotate_90=rotate_90,
            resolution=resolution,
            framerate=current_fps,
            bitrate=bitrate,
            custom_cmd=custom_args,
            logger=self._logger
        )

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=True)
        ]

    def get_assets(self):
        return dict(
            js=["js/rtsp_plugin.js"]
        )

    # BlueprintPlugin mixin - allow anonymous access to stream/snapshot
    def is_blueprint_protected(self):
        return False

    @octoprint.plugin.BlueprintPlugin.route("/snapshot", methods=["GET"])
    def snapshot(self):
        rtsp_url = self._settings.get(["rtsp_url"])
        if not rtsp_url:
            flask.abort(404)

        # Ensure streamor exists and is running
        with self._streamor_lock:
            if not self._streamor:
                self.on_settings_save({})
            if self._streamor and not self._streamor.running:
                self._streamor.start()

        # Wait briefly for first frame if needed
        if self._streamor:
            for _ in range(50):  # Wait up to 5 seconds
                frame = self._streamor.get_snapshot()
                if frame:
                    return flask.Response(frame, mimetype='image/jpeg')
                time.sleep(0.1)

        return flask.abort(503)

    @octoprint.plugin.BlueprintPlugin.route("/control/<direction>", methods=["POST"])
    def control_ptz(self, direction):
        use_ptz = self._settings.get_boolean(["use_ptz"])
        if not use_ptz:
            return flask.Response("PTZ disabled", status=403)

        mapping = {
            "left": "ptz_url_left",
            "right": "ptz_url_right",
            "up": "ptz_url_up",
            "down": "ptz_url_down",
            "zoomin": "ptz_url_zoom_in",
            "zoomout": "ptz_url_zoom_out",
            "home": "ptz_url_home"
        }

        setting_key = mapping.get(direction)
        if not setting_key:
            return flask.Response("Invalid direction", status=400)

        url = self._settings.get([setting_key])
        if not url:
             return flask.Response("URL not configured for this direction", status=400)

        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                pass
            return flask.Response("OK", status=200)
        except Exception as e:
            self._logger.error(f"PTZ Error: {e}")
            return flask.Response(f"Error: {str(e)}", status=502)

    # SoftwareUpdatePlugin mixin
    def get_update_information(self):
        return dict(
            rtsp=dict(
                displayName="OctoPrint-RTSP",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="soopahfly",
                repo="OctoPrint-RTSP",
                current=self._plugin_version,

                # update method: pip from github release zip
                pip="https://github.com/soopahfly/OctoPrint-RTSP/archive/{target_version}.zip"
            )
        )


__plugin_name__ = "OctoPrint-RTSP"
__plugin_pythoncompat__ = ">=3,<4"
__plugin_implementation__ = None
__plugin_hooks__ = None


def __plugin_load__():
    global __plugin_implementation__
    global __plugin_hooks__

    __plugin_implementation__ = RtspPlugin()
    __plugin_hooks__ = {
        "octoprint.server.http.routes": register_custom_routes,
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }


def register_custom_routes(server_routes, *args, **kwargs):
    """Register native Tornado routes for streaming"""
    # Route will be prefixed with /plugin/rtsp/ by OctoPrint
    # Tuple must be (pattern, handler, kwargs_dict)
    return [
        (r"/stream", MjpegStreamHandler, {}),
    ]
