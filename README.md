# OctoPrint-RTSP

This plugin allows you to view RTSP camera streams (like those from Wyze, Ubiquiti, or standard IP security cameras) directly within the OctoPrint interface. 

It solves the common problem where browsers cannot natively display `rtsp://` video streams. The plugin uses **FFmpeg** to transcode the RTSP stream into an MJPEG stream on-the-fly, which can then be viewed in any browser.

## Features

*   **RTSP to MJPEG Transcoding**: View any RTSP stream in Chrome, Firefox, Safari, etc.
*   **Low CPU Broadcast Mode**: A single FFmpeg process serves all connected clients, preventing CPU spikes.
*   **Smart Reconnect**: Automatically attempts to restart the stream if the camera disconnects.
*   **Orientation Control**: Flip Horizontal, Flip Vertical, and Rotate 90° support.
*   **Advanced FFmpeg Tuning**: Custom control over resolution, framerate, and bitrate to optimize for Raspberry Pi hardware.
*   **Snapshot Support**: Provides a static image endpoint for creating time-lapses.
*   **Generic PTZ Control**: Map simple HTTP URL endpoints to on-screen Pan/Tilt/Zoom buttons.

## Prerequisites

*   **FFmpeg**: This plugin relies on `ffmpeg` being installed and available in the system PATH.
    *   **OctoPrint Docker Image**: `ffmpeg` is pre-installed in the official image. No action needed.
    *   **OctoPi**: Install via SSH: `sudo apt update && sudo apt install ffmpeg`
    *   **Windows**: Download FFmpeg and add the `bin` folder to your Windows System PATH.

## Installation

### Manually using the URL
1.  Open the Plugin Manager.
2.  Click "Get More..." and use the **... from URL** option.
3.  Enter: `https://github.com/soopahfly/OctoPrint-RTSP/archive/main.zip`

## Configuration

1.  **RTSP Stream URL**: Go to **Settings > OctoPrint-RTSP** and enter your camera's RTSP URL (e.g., `rtsp://user:pass@192.168.1.50:554/live`).
    *   *Note: If your password contains special characters, you must URL Encode them.*
2.  **Webcam Integration**:
    *   After saving, the plugin shows a **Stream Output URL** (e.g., `/plugin/rtsp/stream`).
    *   Copy this URL.
    *   Go to **Settings > Webcam & Timelapse**.
    *   Paste it into the **Stream URL** field.
    *   Click **Test** to verify.
    *   Don't forget to **Save**!

## Privacy Policy

This plugin:
*   **Does NOT** collect any user data.
*   **Does NOT** connect to any cloud services.
*   **Does NOT** include any tracking or analytics code.
*   Stores your RTSP credentials locally in your OctoPrint `config.yaml`.
*   Proxies the video stream through your OctoPrint server (your camera is not exposed directly to the internet).

## Author

Nathen Fredrick (soopahfly@gmail.com)

## Changelog

### v1.0.0
- **Major**: First stable release
- **Fixed**: MJPEG streaming now uses native Tornado handler (fixes Flask/WSGI buffering issues)
- **Fixed**: Stream now works reliably in OctoPrint's Control tab webcam viewer
- **Improved**: Better frame delivery using Tornado's async I/O

### v0.5.4
- **Fixed**: Blueprint routes now allow anonymous access (was returning 403 Permission Denied)
- **Added**: `is_blueprint_protected()` returns False so stream/snapshot URLs work without login

### v0.5.3
- **Fixed**: Set custom_bindings=True to work with manual ko.applyBindings approach
- **Added**: Standalone test script (tests/test_stream.py) for debugging stream issues

### v0.5.2
- **Fixed**: Manual ko.applyBindings in onSettingsShown to work with custom_bindings=True
- **Fixed**: Settings and URLs now properly display when settings dialog opens

### v0.5.1
- **Fixed**: Preview now uses snapshot endpoint (single JPEG) instead of MJPEG stream
- **Added**: Refresh button for preview image
- **Removed**: Broken stream preview (browsers can't display MJPEG in img tags)

### v0.5.0
- **Fixed**: Complete rewrite of Knockout.js binding approach for `custom_bindings=True`
- **Fixed**: Settings now properly bind through viewmodel's `settings` property
- **Fixed**: Stream/Snapshot URLs now display correctly via direct viewmodel access
- **Fixed**: Added `onBeforeBinding` lifecycle hook for proper settings initialization

### v0.4.4
- **Fixed**: Restored working v0.4.0 template binding pattern with `data-bind="with:"` context
- **Fixed**: Use `$parent.streamUrl` for URL bindings within settings context

### v0.4.3
- **Fixed**: Settings bindings now use correct viewmodel context
- **Fixed**: Simplified template bindings for better compatibility

### v0.4.2
- **Fixed**: URL display bindings now work correctly in settings

### v0.4.1
- **Fixed**: Added cache busting for JavaScript assets

### v0.4.0
- **Fixed**: Snapshot URL now uses correct protocol (HTTPS support)
- **Fixed**: Cross-platform debug paths (Windows/Linux/Docker compatibility)
- **Fixed**: Reduced frame buffer limit from 5MB to 2MB (better for Raspberry Pi)
- **Fixed**: Thread safety improvements for stream initialization
- **Fixed**: Removed debug console.log from production JavaScript
- **Improved**: Thread-safe logging state initialization

### v0.3.4
- Fixed missing return in get_assets

### v0.3.3
- Force cache bust and safer bindings

### v0.3.2
- Fix bindings for real

### v0.3.1
- Fix missing config items and update docs

### v0.3.0
- Initial public release with broadcast mode

## License

AGPLv3
