# -*- coding: utf-8 -*-
from setuptools import setup

plugin_identifier = "rtsp"
plugin_package = "octoprint_rtsp"
plugin_name = "OctoPrint-RTSP"
plugin_version = "1.0.3"
plugin_description = """View RTSP camera streams in OctoPrint using FFmpeg transcoding to MJPEG"""
plugin_author = "Nathen Fredrick"
plugin_author_email = "soopahfly@gmail.com"
plugin_url = "https://github.com/soopahfly/OctoPrint-RTSP"
plugin_license = "AGPLv3"

plugin_requires = [
    "OctoPrint>=1.4.0"
]

plugin_additional_data = []

plugin_additional_packages = []
plugin_ignored_packages = []

additional_setup_parameters = {
    "python_requires": ">=3.7,<4"
}

setup_parameters = {
    "name": plugin_name,
    "version": plugin_version,
    "description": plugin_description,
    "author": plugin_author,
    "author_email": plugin_author_email,
    "url": plugin_url,
    "license": plugin_license,
    "packages": [plugin_package],
    "package_data": {plugin_package: plugin_additional_data},
    "include_package_data": True,
    "zip_safe": False,
    "install_requires": plugin_requires,
    "extras_require": {},
    "entry_points": {
        "octoprint.plugin": [
            f"{plugin_identifier} = {plugin_package}"
        ]
    },
}

setup_parameters.update(additional_setup_parameters)

if __name__ == "__main__":
    setup(**setup_parameters)
