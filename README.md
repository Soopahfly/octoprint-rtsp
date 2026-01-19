# OctoPrint-RTSP

A simple OctoPrint plugin that allows you to view RTSP camera streams (like those from security cameras) directly in the OctoPrint interface.

It works by using **FFmpeg** (which is built-in to the official OctoPrint Docker image) to transcode the RTSP stream into an MJPEG stream that OctoPrint can understand.

## Prerequisites

-   **FFmpeg**: Must be available on the system running OctoPrint.
    -   **Docker**: The official `octoprint/octoprint` image already includes this. No extra setup needed.
    -   **OctoPi**: Install via `sudo apt install ffmpeg`.
    -   **Windows**: Install FFmpeg and add it to your PATH.

## Development

If you are developing this plugin or strictly want to install it manually via command line, it is highly recommended to use OctoPrint's virtual environment to avoid permission issues and the "running pip as root" warning.

**On OctoPi:**
```bash
source ~/oprint/bin/activate
pip install -e .
```

**On Windows:**
```powershell
.\venv\Scripts\activate
pip install -e .
```

## Installation

1.  **Download**: Download the `OctoPrint-RTSP-0.3.4.zip` file from this repository (or click [here](./OctoPrint-RTSP-0.3.4.zip) if viewing on GitHub).
2.  **Upload**:
    -   Open OctoPrint Settings (Wrench icon).
    -   Go to **Plugin Manager**.
    -   Click **Get More...**.
    -   Scroll down to **... from an uploaded file**.
    -   Select the downloaded `.zip` file.
3.  **Restart**: Restart OctoPrint when prompted.

## Configuration

1.  **Set RTSP URL**:
    -   Go to **Settings** > **OctoPrint-RTSP**.
    -   Enter your camera's RTSP URL (e.g., `rtsp://username:password@192.168.1.50:554/stream`).
    -   Click **Save**.
2.  **Set Webcam URL**:
    -   After saving, the plugin will display a **Stream Output URL** (e.g., `http://YOUR_IP/plugin/rtsp/stream`).
    -   Copy this URL.
    -   Go to **Settings** > **Webcam & Timelapse**.
    -   Paste the URL into the **Stream URL** field.
    -   Click **Test** to verify the video works.
    -   Click **Save**.
3.  **Set Snapshot URL**:
    -   Copy the **Snapshot Output URL** (e.g., `http://YOUR_IP/plugin/rtsp/snapshot`).
    -   Paste it into the **Snapshot URL** field in Webcam settings.
    -   Click **Test** to verify.

## Privacy & Security

-   **Log Redaction**: RTSP credentials are masked in the OctoPrint logs (e.g., `rtsp://user:****@ip`).
-   **Security**: The plugin proxies the stream, so your camera is not directly exposed to the browser client.

## Changelog

### v0.3.4
-   **CRITICAL FIX**: Fixed broken asset loading that caused blank settings in v0.3.3.

### v0.3.3
-   **Bug Fix**: Renamed JS file to force cache clear and implemented safer UI binding logic.

### v0.3.2
-   **Bug Fix**: Robust fix for blank settings screen by refactoring ViewModel bindings.

### v0.3.1
-   **Bug Fix**: Fixed missing configuration items (Blank settings page).
-   **Documentation**: Updated installation instructions for developers.

### v0.3.0
-   **Major Performance Upgrade**: Rewritten with Broadcast architecture. A single FFmpeg process now serves all clients, drastically reducing CPU usage.
-   **Advanced Settings**: Added ability to control FFmpeg resolution, framerate, and bitrate to optimize for your hardware.
-   **Stability**: Added "Smart Reconnect" logic to automatically restart the stream if it freezes.
-   **Feature**: Added Generic PTZ Control support. Configure HTTP URLs to control your camera directly from settings (Test buttons included).

### v0.2.0
-   **New Feature**: Added Snapshot support (`/snapshot` endpoint).
-   **New Feature**: Added Image Orientation settings (Flip Horizontal, Flip Vertical, Rotate 90°).
-   **Security**: Implemented credential redaction in logs.
-   **Improvement**: Switched to FFmpeg for robust transcoding.

### v0.1.0
-   Initial release with basic RTSP to MJPEG streaming.

-   **Gray Screen / No Image**:
    -   Check your OctoPrint logs (`octoprint.log`). If you see "FFmpeg not found", make sure FFmpeg is installed and in your system PATH.
    -   Verify your RTSP URL works in a desktop player like VLC.
-   **High CPU Usage**:
    -   Transcoding is CPU intensive. If running on a Raspberry Pi Zero or older Pi, this might be too heavy. Consider reducing the resolution on your camera settings.
