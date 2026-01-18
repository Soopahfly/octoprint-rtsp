# -*- coding: utf-8 -*-
import subprocess
import logging
import shlex

class Streamor:
    def __init__(self, url, logger=None):
        self.url = url
        self.logger = logger or logging.getLogger(__name__)
        self.running = True
        self.process = None

    def stop(self):
        self.running = False
        if self.process:
            self.process.kill()
            self.process = None

    def generate(self):
        # Build FFmpeg command
        # -i url: input url
        # -f mjpeg: output format mjpeg
        # -q:v 5: video quality (1-31, lower is better quality)
        # -r 15: framerate
        # pipe:1: output to stdout
        
        # We need to ensure we don't just dump raw jpeg data continuously without boundaries if we want to manually yield frames,
        # BUT simpler approach for mjpeg stream: let ffmpeg generate the mjpeg stream and we just passthrough?
        # A common mjpeg stream is just concatenated jpegs.
        # However, for a flask generator, we usually need to yield chunk by chunk with a boundary.
        
        # Method 1: Ask ffmpeg to output 'image2pipe' with codec 'mjpeg'. This essentially dumps raw jpegs one after another.
        # We need to find the JPEG SOI and EOI markers to split them into frames.
        
        command = [
            'ffmpeg',
            '-y',
            '-rtsp_transport', 'tcp', # Force TCP for better stability
            '-i', self.url,
            '-f', 'image2pipe',
            '-vcodec', 'mjpeg',
            '-q:v', '5',
            '-r', '15',
            '-'
        ]
        
        if self.logger:
            self.logger.info(f"Starting legacy stream: {shlex.join(command)}")

        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, # Capture stderr to avoid log spam, or redirect to log
                bufsize=10**6 # buffer size
            )
        except FileNotFoundError:
             if self.logger:
                 self.logger.error("FFmpeg not found. Please ensure ffmpeg is installed.")
             return

        # Simple JPEG parsing
        # SOI = \xff\xd8
        # EOI = \xff\xd9
        
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
                    # No start marker found.
                    # Keep the last byte just in case SOI is split across chunks
                    if len(buffer) > 1:
                        buffer = buffer[-1:]
                    break
                
                # Discard data before SOI
                if a > 0:
                    buffer = buffer[a:]
                
                # Now SOI is at index 0. Look for EOI.
                b = buffer.find(b'\xff\xd9')
                if b == -1:
                    # No EOI yet, need more data
                    break
                
                # Extract frame
                jpg = buffer[:b+2]
                buffer = buffer[b+2:]
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n')

        if self.process:
            self.process.kill()
