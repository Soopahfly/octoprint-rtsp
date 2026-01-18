# OctoPrint-RTSP

A simple OctoPrint plugin that allows you to view RTSP camera streams (like those from security cameras) directly in the OctoPrint interface.

It works by using **FFmpeg** (which is built-in to the official OctoPrint Docker image) to transcode the RTSP stream into an MJPEG stream that OctoPrint can understand.

## Prerequisites

-   **FFmpeg**: Must be available on the system running OctoPrint.
    -   **Docker**: The official `octoprint/octoprint` image already includes this. No extra setup needed.
    -   **OctoPi**: Install via `sudo apt install ffmpeg`.
    -   **Windows**: Install FFmpeg and add it to your PATH.

## Installation

1.  **Download**: Download the `OctoPrint-RTSP-0.2.0.zip` file from this repository (or click [here](./OctoPrint-RTSP-0.2.0.zip) if viewing on GitHub).
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
