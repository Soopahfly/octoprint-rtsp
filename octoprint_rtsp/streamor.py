# -*- coding: utf-8 -*-
import subprocess
import logging
import shlex
import threading
import time
import tempfile
import os

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

        # Debug frame path (cross-platform)
        self._debug_frame_path = os.path.join(tempfile.gettempdir(), "octoprint_rtsp_debug_frame.jpg")

        self.running = False
        self.process = None
        self.thread = None
        
        # Broadcast mechanism
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self.last_frame = None

        # Thread-safe logging state (initialized once to avoid race conditions)
        self._last_log_time = 0
        self._last_yield_log = 0
        self._debug_saved = False

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
            '-rtsp_flags', 'prefer_tcp',
            '-stimeout', '5000000',
            '-i', self.url,
            '-f', 'image2pipe',
            '-pix_fmt', 'yuv420p',
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
        if self.url == "TEST":
            self.logger.info("Streamor: Starting TEST PATTERN mode")
            # Try to load debug frame or use a fallback (minimal white pixel)
            fallback = b'\xff\xd8\xff\xe0\x00\x10\x4a\x46\x49\x46\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00\xff\xdb\x00\x43\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01\x7d\x01\x02\x03\x00\x04\x11\x05\x12\x21\x31\x41\x06\x13\x51\x61\x07\x22\x71\x14\x32\x81\x91\xa1\x08\x23\x42\xb1\xc1\x15\x52\xd1\xf0\x24\x33\x62\x72\x82\x09\x0a\x16\x17\x18\x19\x1a\x25\x26\x27\x28\x29\x2a\x34\x35\x36\x37\x38\x39\x3a\x43\x44\x45\x46\x47\x48\x49\x4a\x53\x54\x55\x56\x57\x58\x59\x5a\x63\x64\x65\x66\x67\x68\x69\x6a\x73\x74\x75\x76\x77\x78\x79\x7a\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00\xfc\xfc\x3f\xff\xd9'
            
            frame = fallback
            try:
                with open(self._debug_frame_path, "rb") as f:
                    frame = f.read()
            except Exception:
                self.logger.warning(f"No debug frame found at {self._debug_frame_path}, using fallback")

            while self.running:
                with self._condition:
                    self.last_frame = frame
                    self._condition.notify_all()
                time.sleep(1.0 / (self.framerate if self.framerate else 15))
            return

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
                    stderr=subprocess.PIPE,
                    bufsize=10**6
                )
                
                # Start stderr reader thread
                self._stderr_thread = threading.Thread(target=self._monitor_stderr)
                self._stderr_thread.daemon = True
                self._stderr_thread.start()
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
            chunk_size = 32768 # Increased chunk size for better performance

            while self.running and self.process.poll() is None:
                try:
                    data = self.process.stdout.read(chunk_size)
                    if not data:
                        break # EOF
                    buffer += data
                    
                    while True:
                        a = buffer.find(b'\xff\xd8')
                        if a == -1:
                            if len(buffer) > 4096: # Prevent buffer from growing infinitely if no headers found
                                buffer = buffer[-4096:]
                            break
                        
                        if a > 0:
                            buffer = buffer[a:]
                        
                        b = buffer.find(b'\xff\xd9')
                        if b == -1:
                            # We found start, but not end. Keep reading.
                            # Safety: if frame is too huge (e.g. > 2MB), drop it
                            # Typical MJPEG frames are 50-300KB; 2MB indicates malformed data
                            if len(buffer) > 2000000:
                                self.logger.warning("Streamor: Frame exceeded 2MB limit, dropping buffer")
                                buffer = b''
                            break
                        
                        jpg = buffer[:b+2]
                        buffer = buffer[b+2:]
                        
                        with self._condition:
                            self.last_frame = jpg
                            self._condition.notify_all()
                        
                        # Debug logging (rate limited)
                        if self._last_log_time < time.time() - 5:
                            self.logger.info(f"Streamor: Frame captured! Size: {len(jpg)} bytes")
                            self._last_log_time = time.time()

                            # DEBUG: Save first frame to disk
                            if not self._debug_saved:
                                try:
                                    with open(self._debug_frame_path, "wb") as f:
                                        f.write(jpg)
                                    self._debug_saved = True
                                    self.logger.info(f"Streamor: Saved debug frame to {self._debug_frame_path}")
                                except Exception as e:
                                    self.logger.error(f"Failed to save debug frame: {e}")
                            
                except Exception as e:
                    self.logger.error(f"Streamor read error: {e}")
                    break
            
            # Process died or we stopped
            if self.process:
                self.process.terminate()
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
                         # Strict MJPEG format with Content-Length
                         # Strict MJPEG format
                         # Boundary: OctoPrintStream (defined in __init__.py)
                         # Structure: --Boundary\r\nHeaders\r\n\r\nData\r\n
                         
                         header = (b'--OctoPrintStream\r\n' +
                                   b'Content-Type: image/jpeg\r\n' +
                                   f'Content-Length: {len(self.last_frame)}\r\n\r\n'.encode('utf-8'))
                                   
                         frame_data = header + self.last_frame + b'\r\n'
                         
                         if self._last_yield_log < time.time() - 5:
                             self.logger.info(f"Streamor: Yielding frame. Header len: {len(header)}, Body len: {len(self.last_frame)}")
                             self._last_yield_log = time.time()
                             
                         yield frame_data
                else:
                    # Timeout (stream stalled?) - Yield nothing or keep waiting
                    continue

    def _monitor_stderr(self):
        """Reads stderr from the ffmpeg process and logs it."""
        if not self.process or not self.process.stderr:
            return

        try:
            for line in iter(self.process.stderr.readline, b''):
                if line:
                    line_str = line.decode('utf-8', errors='ignore').strip()
                    self.logger.info(f"FFmpeg: {line_str}")
        except Exception as e:
            self.logger.error(f"Error reading stderr: {e}")

