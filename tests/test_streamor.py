import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import time
import threading

# Add package to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from octoprint_rtsp.streamor import Streamor

class TestStreamor(unittest.TestCase):
    @patch('subprocess.Popen')
    def test_broadcast_stream(self, mock_popen):
        # Setup mock process
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        
        # We need the read to return a frame, then maybe block or yield empty?
        # If we yield empty, it triggers reconnect logic which sleeps.
        # Let's make it return a frame once, then kept alive (return nothing/block)
        # To avoid infinite loop in test, we control it via side_effect that checks a flag or just use a list
        
        # valid jpeg
        frame_data = b'\xff\xd8fakejpg\xff\xd9'
        
        def side_effect(*args):
             # Return frame once
             if not hasattr(side_effect, 'called'):
                 side_effect.called = True
                 return frame_data
             # Then simulate waiting for next frame (return nothing after a delay?)
             # Or just empty bytes? Empty bytes = EOF.
             # Let's return empty bytes to simulate EOF, but catch the thread before it restarts
             time.sleep(0.1) 
             return b''

        mock_process.stdout.read.side_effect = side_effect
        mock_popen.return_value = mock_process

        # Initialize streamor
        s = Streamor("rtsp://fake")
        
        # Start background thread
        s.start()
        
        # Get generator
        gen = s.generate()
        
        # Try to get one frame
        # The thread should read the frame, notify, and we receive it.
        try:
            frame = next(gen)
            self.assertIn(b'fakejpg', frame)
            self.assertIn(b'Content-Type: image/jpeg', frame)
        except StopIteration:
            self.fail("Generator stopped unexpectedly")
        
        # Clean up
        s.stop()

if __name__ == '__main__':
    unittest.main()
