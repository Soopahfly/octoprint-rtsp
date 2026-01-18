# -*- coding: utf-8 -*-
from __future__ import absolute_import

import octoprint.plugin
import flask
from .streamor import Streamor

class RtspPlugin(octoprint.plugin.StartupPlugin,
                 octoprint.plugin.SettingsPlugin,
                 octoprint.plugin.AssetPlugin,
                 octoprint.plugin.TemplatePlugin,
                 octoprint.plugin.BlueprintPlugin):

    def __init__(self):
        self._streamor = None

    def on_after_startup(self):
        self._logger.info("OctoPrint-RTSP loaded!")
        rtsp_url = self._settings.get(["rtsp_url"])
        if rtsp_url:
            self._logger.info(f"RTSP URL configured: {rtsp_url}")
            self._streamor = Streamor(rtsp_url, self._logger)

    def get_settings_defaults(self):
        return dict(
            rtsp_url="",
            username="",
            password="",
            stream_fps=15,
            flip_h=False,
            flip_v=False,
            rotate_90=False
        )
    
    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        # Re-initialize streamor if settings changed
        rtsp_url = self._settings.get(["rtsp_url"])
        flip_h = self._settings.get_boolean(["flip_h"])
        flip_v = self._settings.get_boolean(["flip_v"])
        rotate_90 = self._settings.get_boolean(["rotate_90"])

        if self._streamor:
            self._streamor.stop()
        self._streamor = Streamor(rtsp_url, flip_h, flip_v, rotate_90, self._logger)

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    def get_assets(self):
        return dict(
            js=["js/rtsp.js"]
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

    @octoprint.plugin.BlueprintPlugin.route("/stream", methods=["GET"])
    def stream_video(self):
        rtsp_url = self._settings.get(["rtsp_url"])
        flip_h = self._settings.get_boolean(["flip_h"])
        flip_v = self._settings.get_boolean(["flip_v"])
        rotate_90 = self._settings.get_boolean(["rotate_90"])

        if not rtsp_url:
            return flask.Response("RTSP URL not configured", status=400)
        
        if not self._streamor:
             self._streamor = Streamor(rtsp_url, flip_h, flip_v, rotate_90, self._logger)

        return flask.Response(self._streamor.generate(),
                              mimetype='multipart/x-mixed-replace; boundary=frame')

__plugin_name__ = "OctoPrint-RTSP"
__plugin_pythoncompat__ = ">=3,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = RtspPlugin()
