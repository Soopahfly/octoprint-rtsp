# -*- coding: utf-8 -*-
from setuptools import setup

plugin_identifier = "rtsp"
plugin_package = "octoprint_rtsp"
plugin_name = "OctoPrint-RTSP"
plugin_version = "0.4.0"
plugin_description = """Allows viewing RTSP camera streams in OctoPrint via OpenCV transcoding"""
plugin_author = "Antigravity"
plugin_author_email = "antigravity@example.com"
plugin_url = "https://github.com/soopahfly/OctoPrint-RTSP"
plugin_license = "AGPLv3"

setup_parameters = {
    "name": plugin_name,
    "version": plugin_version,
    "description": plugin_description,
    "author": plugin_author,
    "author_email": plugin_author_email,
    "url": plugin_url,
    "license": plugin_license,
    "packages": [plugin_package],
    "include_package_data": True,
    "zip_safe": False,
    "install_requires": [
        "OctoPrint"
    ],
    "entry_points": {
        "octoprint.plugin": [
            "rtsp = octoprint_rtsp"
        ]
    },
}

if __name__ == "__main__":
    setup(**setup_parameters)
