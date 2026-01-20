# -*- coding: utf-8 -*-
from __future__ import absolute_import

import threading
import octoprint.plugin
import flask
import urllib.request
import urllib.error
from .streamor import Streamor

class RtspPlugin(octoprint.plugin.StartupPlugin,
                 octoprint.plugin.SettingsPlugin,
                 octoprint.plugin.AssetPlugin,
                 octoprint.plugin.TemplatePlugin,
                 octoprint.plugin.BlueprintPlugin):

    def __init__(self):
        self._streamor = None
        self._streamor_lock = threading.Lock()

    def on_after_startup(self):
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
        # Don't start it yet, wait for first connection? 
        # Or start it immediately if we assume user wants it always on?
        # Broadcast mode is efficient, but let's lazy start on first request.

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=True)
        ]

    def get_assets(self):
        return dict(
            js=["js/rtsp_plugin.js?v=0.5.1"]
        )

    # BlueprintPlugin mixin
    @octoprint.plugin.BlueprintPlugin.route("/snapshot", methods=["GET"])
    def snapshot(self):
        if not self._streamor:
            rtsp_url = self._settings.get(["rtsp_url"])
            if not rtsp_url:
                flask.abort(404)
            # Initialize on demand? ideally assume running
            return flask.abort(503) # Service unavailable if not streaming
        
        frame = self._streamor.get_snapshot()
        if frame:
             return flask.Response(frame, mimetype='image/jpeg')
        return flask.abort(404)

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
            # We don't care about the response, just firing the hook
            with urllib.request.urlopen(url, timeout=5) as response:
                pass
            return flask.Response("OK", status=200)
        except Exception as e:
            self._logger.error(f"PTZ Error: {e}")
            return flask.Response(f"Error: {str(e)}", status=502)

    @octoprint.plugin.BlueprintPlugin.route("/stream", methods=["GET"])
    def stream_video(self):
        self._logger.info("Stream request received!")
        rtsp_url = self._settings.get(["rtsp_url"])

        if not rtsp_url:
            self._logger.warning("Stream request failed: No RTSP URL")
            return flask.Response("RTSP URL not configured", status=400)

        # Thread-safe streamor initialization
        with self._streamor_lock:
            if not self._streamor:
                # We need to load all settings to init it correctly.
                # Ideally this is done in on_after_startup, but for safety:
                self.on_settings_save({})
                if not self._streamor:
                    self._logger.error("Streamor failed to initialize")
                    return flask.Response("Streamor init failed", status=500)

            # Ensure broadcast thread is running
            self._streamor.start()
        
        self._logger.info("Serving stream...")
        response = flask.Response(flask.stream_with_context(self._streamor.generate()),
                                  mimetype='multipart/x-mixed-replace; boundary=OctoPrintStream')
        response.direct_passthrough = True
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate' 
        response.headers['Pragma'] = 'no-cache' 
        response.headers['Expires'] = '0'
        return response

__plugin_name__ = "OctoPrint-RTSP"
__plugin_pythoncompat__ = ">=3,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = RtspPlugin()
