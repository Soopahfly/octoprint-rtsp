# -*- coding: utf-8 -*-
import subprocess
import logging
import shlex
import threading
import time

class Streamor:
    def __init__(self, url, flip_h=False, flip_v=False, rotate_90=False, logger=None):
        self.url = url
        self.flip_h = flip_h
        self.flip_v = flip_v
        self.rotate_90 = rotate_90
        self.logger = logger or logging.getLogger(__name__)
        
        self.running = True
        self.process = None
        self.last_frame = None
        self._lock = threading.Lock()

    def _sanitize_url(self, url):
        # Mask password in rtsp://user:pass@host format
        try:
            if "@" in url and "://" in url:
                prefix = url.split("://")[0]
                rest = url.split("://")[1]
                if "@" in rest:
                    auth, host = rest.split("@", 1)
                    if ":" in auth:
                        user, _ = auth.split(":", 1)
                        return f"{prefix}://{user}:****@{host}"
            return url
        except Exception:
            return "rtsp://***"

    def stop(self):
        self.running = False
        if self.process:
            self.process.kill()
            self.process = None

    def get_snapshot(self):
        with self._lock:
            return self.last_frame

    def generate(self):
        # Build FFmpeg filters
        filters = []
        if self.flip_h:
            filters.append("hflip")
        if self.flip_v:
            filters.append("vflip")
        if self.rotate_90:
            filters.append("transpose=1") # 90 degrees clockwise

        filter_arg = []
        if filters:
            filter_arg = ['-vf', ",".join(filters)]

        command = [
            'ffmpeg',
            '-y',
            '-rtsp_transport', 'tcp',
            '-i', self.url,
            '-f', 'image2pipe',
            '-vcodec', 'mjpeg',
            '-q:v', '5',
            '-r', '15'
        ] + filter_arg + ['-']
        
        if self.logger:
            safe_cmd = list(command)
            # Find the url index and replace it for logging
            for i, arg in enumerate(safe_cmd):
                if arg == self.url:
                    safe_cmd[i] = self._sanitize_url(self.url)
            self.logger.info(f"Starting stream: {shlex.join(safe_cmd)}")

        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, # Suppress stderr to avoid log spam
                bufsize=10**6
            )
        except FileNotFoundError:
             if self.logger:
                 self.logger.error("FFmpeg not found. Please ensure ffmpeg is installed.")
             return

        buffer = b''
        chunk_size = 4096
        
        while self.running:
            data = self.process.stdout.read(chunk_size)
            if not data:
                break
            buffer += data
            
            while True:
                a = buffer.find(b'\xff\xd8')
                if a == -1:
                    if len(buffer) > 1:
                        buffer = buffer[-1:]
                    break
                
                if a > 0:
                    buffer = buffer[a:]
                
                b = buffer.find(b'\xff\xd9')
                if b == -1:
                    break
                
                jpg = buffer[:b+2]
                buffer = buffer[b+2:]
                
                # Cache for snapshot
                with self._lock:
                    self.last_frame = jpg

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n')

        if self.process:
            self.process.kill()
