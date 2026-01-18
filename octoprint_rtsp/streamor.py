# -*- coding: utf-8 -*-
import subprocess
import logging
import shlex
import threading
import time

class Streamor:
    def __init__(self, url, flip_h=False, flip_v=False, rotate_90=False, 
                 resolution=None, framerate=15, bitrate=None, custom_cmd=None,
                 logger=None):
        self.url = url
        self.flip_h = flip_h
        self.flip_v = flip_v
        self.rotate_90 = rotate_90
        # Advanced settings
        self.resolution = resolution # e.g. "640x480"
        self.framerate = framerate or 15
        self.bitrate = bitrate # e.g. "1000k"
        self.custom_cmd = custom_cmd

        self.logger = logger or logging.getLogger(__name__)
        
        self.running = False
        self.process = None
        self.thread = None
        
        # Broadcast mechanism
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self.last_frame = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        if self.process:
            self.process.kill()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.process = None
        self.thread = None

    def get_snapshot(self):
        with self._lock:
            return self.last_frame

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

    def _build_command(self):
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

        # Base args
        args = [
            'ffmpeg',
            '-y',
            '-rtsp_transport', 'tcp',
            '-i', self.url,
            '-f', 'image2pipe',
            '-vcodec', 'mjpeg',
            '-q:v', '5',
        ]

        if self.framerate:
             args.extend(['-r', str(self.framerate)])
        
        if self.resolution:
             args.extend(['-s', self.resolution])
             
        if self.bitrate:
             args.extend(['-b:v', self.bitrate])

        # Add filters
        args.extend(filter_arg)

        # Output to pipe
        args.append('-')
        
        # If user provides a totally custom command string, we might override (advanced)
        # For now, let's keep it simple: if custom_cmd is set, maybe append? 
        # But safest is to just stick to our builder for now unless requested otherwise.
        # Let's support appending extra raw args if needed, or replacing if very advanced.
        # Actually, let's allow `custom_cmd` to be extra arguments appended before output.
        if self.custom_cmd:
             # careful splitting
             extra = shlex.split(self.custom_cmd)
             # Insert before output '-'
             args = args[:-1] + extra + args[-1:]

        return args

    def _capture_loop(self):
        while self.running:
            command = self._build_command()
            
            if self.logger:
                safe_cmd = list(command)
                for i, arg in enumerate(safe_cmd):
                    if arg == self.url:
                        safe_cmd[i] = self._sanitize_url(self.url)
                self.logger.info(f"Streamor: Starting ffmpeg: {shlex.join(safe_cmd)}")
            
            try:
                self.process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    bufsize=10**6
                )
            except FileNotFoundError:
                if self.logger:
                    self.logger.error("FFmpeg not found. Retrying in 5s...")
                time.sleep(5)
                continue
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error starting ffmpeg: {e}")
                time.sleep(5)
                continue

            buffer = b''
            chunk_size = 4096

            while self.running and self.process.poll() is None:
                try:
                    data = self.process.stdout.read(chunk_size)
                    if not data:
                        break # EOF
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
                        
                        with self._lock:
                            self.last_frame = jpg
                            self._condition.notify_all()
                            
                except Exception as e:
                    self.logger.error(f"Streamor read error: {e}")
                    break
            
            # Process died or we stopped
            if self.process:
                self.process.kill()
                self.process = None
            
            if self.running:
                self.logger.info("Streamor: FFmpeg exited. Restarting in 2s...")
                time.sleep(2) # Smart Reconnect delay

    def generate(self):
        """Generator that yields MJPEG frames from the broadcast thread"""
        while self.running:
            with self._condition:
                if not self.thread or not self.thread.is_alive():
                    # Thread died unexpectedly?
                    break
                    
                # Wait for next frame
                if self._condition.wait(timeout=5.0):
                     # Got frame
                     if self.last_frame:
                         yield (b'--frame\r\n'
                                b'Content-Type: image/jpeg\r\n\r\n' + self.last_frame + b'\r\n')
                else:
                    # Timeout (stream stalled?) - Yield nothing or keep waiting
                    continue
