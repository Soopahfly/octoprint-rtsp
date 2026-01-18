import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add package to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from octoprint_rtsp.streamor import Streamor

class TestStreamor(unittest.TestCase):
    @patch('subprocess.Popen')
    def test_generate(self, mock_popen):
        # Setup mock process
        mock_process = MagicMock()
        mock_process.stdout.read.side_effect = [
            b'--frame\r\n\xff\xd8fakejpg\xff\xd9', # chunk 1
            b'', # chunk 2 (EOF)
        ]
        
        mock_popen.return_value = mock_process

        # Initialize streamor
        s = Streamor("rtsp://fake")
        
        # Generator
        gen = s.generate()
        
        # Get first frame
        # Our generator logic in streamor.py looks for \xff\xd8 and \xff\xd9
        # The mock data above provides exactly one frame
        frame = next(gen)
        
        # Check format
        self.assertTrue(frame.startswith(b'--frame\r\n'))
        self.assertIn(b'Content-Type: image/jpeg', frame)
        self.assertIn(b'fakejpg', frame)
        
        # Stop
        s.stop()

if __name__ == '__main__':
    unittest.main()
