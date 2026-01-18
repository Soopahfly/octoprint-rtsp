# OctoPrint-RTSP

A simple OctoPrint plugin that allows you to view RTSP camera streams (like those from security cameras) directly in the OctoPrint interface.

It works by using **FFmpeg** (which is built-in to the official OctoPrint Docker image) to transcode the RTSP stream into an MJPEG stream that OctoPrint can understand.

## Prerequisites

-   **FFmpeg**: Must be available on the system running OctoPrint.
    -   **Docker**: The official `octoprint/octoprint` image already includes this. No extra setup needed.
    -   **OctoPi**: Install via `sudo apt install ffmpeg`.
    -   **Windows**: Install FFmpeg and add it to your PATH.

## Installation

1.  **Download**: Download the `OctoPrint-RTSP.zip` file from this repository (or click [here](./OctoPrint-RTSP.zip) if viewing on GitHub).
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

## Troubleshooting

-   **Gray Screen / No Image**:
    -   Check your OctoPrint logs (`octoprint.log`). If you see "FFmpeg not found", make sure FFmpeg is installed and in your system PATH.
    -   Verify your RTSP URL works in a desktop player like VLC.
-   **High CPU Usage**:
    -   Transcoding is CPU intensive. If running on a Raspberry Pi Zero or older Pi, this might be too heavy. Consider reducing the resolution on your camera settings.
