#!/usr/bin/env python3
"""
Standalone test script for OctoPrint-RTSP streaming.

This script tests the stream pipeline independently of OctoPrint to help
diagnose issues. Run it from the command line with your RTSP URL.

Usage:
    python test_stream.py rtsp://user:pass@192.168.1.100:554/live
    python test_stream.py TEST  # Use test pattern mode
    python test_stream.py --raw rtsp://...  # Test raw FFmpeg output first

Tests performed:
    1. FFmpeg availability check
    2. RTSP connection test (ffprobe)
    3. Raw FFmpeg capture test (bypasses Streamor)
    4. Frame capture verification (using Streamor)
    5. JPEG validity check
    6. Saves test frames to disk for inspection
"""

import sys
import os
import time
import subprocess
import logging

# Add parent directory to path so we can import streamor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from octoprint_rtsp.streamor import Streamor

# Setup logging to see everything
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def check_ffmpeg():
    """Test 1: Check if FFmpeg is installed and accessible"""
    logger.info("=" * 60)
    logger.info("TEST 1: Checking FFmpeg installation...")
    logger.info("=" * 60)

    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            # Get first line of version info
            version_line = result.stdout.split('\n')[0]
            logger.info(f"SUCCESS: {version_line}")
            return True
        else:
            logger.error(f"FAILED: FFmpeg returned error code {result.returncode}")
            logger.error(f"stderr: {result.stderr}")
            return False
    except FileNotFoundError:
        logger.error("FAILED: FFmpeg not found in PATH")
        logger.error("Install FFmpeg and ensure it's in your system PATH")
        return False
    except Exception as e:
        logger.error(f"FAILED: Error checking FFmpeg: {e}")
        return False

def test_raw_ffmpeg(url, output_dir, duration=5):
    """Test 2.5: Raw FFmpeg capture without Streamor"""
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"TEST 2.5: Raw FFmpeg capture test ({duration}s)...")
    logger.info("=" * 60)

    if url == "TEST":
        logger.info("SKIPPED: Using TEST pattern mode")
        return True

    output_file = os.path.join(output_dir, "raw_ffmpeg_test.jpg")

    # Simple FFmpeg command to grab a single frame
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite
        '-rtsp_transport', 'tcp',
        '-i', url,
        '-frames:v', '1',  # Just one frame
        '-f', 'image2',
        output_file
    ]

    # Sanitize for logging
    safe_cmd = list(cmd)
    for i, arg in enumerate(safe_cmd):
        if arg == url:
            safe_cmd[i] = sanitize_url(url)
    logger.info(f"Running: {' '.join(safe_cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=duration + 10
        )

        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            size = os.path.getsize(output_file)
            logger.info(f"SUCCESS: Captured frame to {output_file} ({size} bytes)")
            return True
        else:
            logger.error("FAILED: No output file created")
            logger.error(f"FFmpeg stderr: {result.stderr[-500:] if result.stderr else 'empty'}")
            return False

    except subprocess.TimeoutExpired:
        logger.error(f"FAILED: FFmpeg timed out after {duration + 10} seconds")
        return False
    except Exception as e:
        logger.error(f"FAILED: {e}")
        return False


def sanitize_url(url):
    """Mask password in RTSP URL for logging"""
    if "@" in url and "://" in url:
        try:
            prefix = url.split("://")[0]
            rest = url.split("://")[1]
            if "@" in rest:
                auth, host = rest.split("@", 1)
                if ":" in auth:
                    user, _ = auth.split(":", 1)
                    return f"{prefix}://{user}:****@{host}"
        except:
            pass
    return "rtsp://***"


def test_rtsp_connection(url):
    """Test 2: Test RTSP connection with FFprobe"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("TEST 2: Testing RTSP connection with ffprobe...")
    logger.info("=" * 60)

    if url == "TEST":
        logger.info("SKIPPED: Using TEST pattern mode (no RTSP URL)")
        return True

    safe_url = sanitize_url(url)
    logger.info(f"Testing URL: {safe_url}")

    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-rtsp_transport', 'tcp',
                '-v', 'error',
                '-show_entries', 'stream=codec_name,width,height',
                '-of', 'default=noprint_wrappers=1',
                '-timeout', '5000000',
                url
            ],
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode == 0 and result.stdout.strip():
            logger.info("SUCCESS: RTSP stream is accessible")
            for line in result.stdout.strip().split('\n'):
                logger.info(f"  Stream info: {line}")
            return True
        else:
            logger.error("FAILED: Could not connect to RTSP stream")
            if result.stderr:
                logger.error(f"  Error: {result.stderr.strip()}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("FAILED: Connection timed out after 15 seconds")
        return False
    except FileNotFoundError:
        logger.warning("WARNING: ffprobe not found, skipping connection test")
        return True  # Don't fail the whole test
    except Exception as e:
        logger.error(f"FAILED: {e}")
        return False

def test_frame_capture(url, duration=10):
    """Test 3: Test frame capture using Streamor"""
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"TEST 3: Testing frame capture for {duration} seconds...")
    logger.info("=" * 60)

    streamor = Streamor(url=url, logger=logger)

    logger.info("Starting streamor...")
    streamor.start()

    frames_received = 0
    frame_sizes = []
    start_time = time.time()
    last_report = start_time

    try:
        while time.time() - start_time < duration:
            frame = streamor.get_snapshot()
            if frame:
                if len(frame_sizes) == 0 or frame != streamor.last_frame:
                    frames_received += 1
                    frame_sizes.append(len(frame))

            # Progress report every 2 seconds
            if time.time() - last_report >= 2:
                elapsed = time.time() - start_time
                logger.info(f"  Progress: {frames_received} frames in {elapsed:.1f}s")
                last_report = time.time()

            time.sleep(0.1)

    finally:
        logger.info("Stopping streamor...")
        streamor.stop()

    if frames_received > 0:
        avg_size = sum(frame_sizes) / len(frame_sizes)
        fps = frames_received / duration
        logger.info(f"SUCCESS: Received {frames_received} frames")
        logger.info(f"  Average frame size: {avg_size/1024:.1f} KB")
        logger.info(f"  Effective FPS: {fps:.1f}")
        logger.info(f"  Min frame size: {min(frame_sizes)/1024:.1f} KB")
        logger.info(f"  Max frame size: {max(frame_sizes)/1024:.1f} KB")
        return True, streamor
    else:
        logger.error("FAILED: No frames received!")
        logger.error("  Check the FFmpeg output above for errors")
        return False, streamor

def test_jpeg_validity(streamor):
    """Test 4: Verify the captured frame is a valid JPEG"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("TEST 4: Validating JPEG frame data...")
    logger.info("=" * 60)

    frame = streamor.get_snapshot()
    if not frame:
        logger.error("FAILED: No frame available to validate")
        return False

    # Check JPEG markers
    has_soi = frame[:2] == b'\xff\xd8'  # Start of Image
    has_eoi = frame[-2:] == b'\xff\xd9'  # End of Image

    if has_soi and has_eoi:
        logger.info("SUCCESS: Frame has valid JPEG markers")
        logger.info(f"  SOI marker: {has_soi} (0xFF 0xD8)")
        logger.info(f"  EOI marker: {has_eoi} (0xFF 0xD9)")
        logger.info(f"  Frame size: {len(frame)} bytes")
        return True
    else:
        logger.error("FAILED: Invalid JPEG data")
        logger.error(f"  SOI marker present: {has_soi}")
        logger.error(f"  EOI marker present: {has_eoi}")
        logger.error(f"  First 20 bytes: {frame[:20].hex()}")
        logger.error(f"  Last 20 bytes: {frame[-20:].hex()}")
        return False

def save_test_frame(streamor, output_dir):
    """Test 5: Save a test frame to disk"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("TEST 5: Saving test frame to disk...")
    logger.info("=" * 60)

    frame = streamor.get_snapshot()
    if not frame:
        logger.error("FAILED: No frame available to save")
        return False

    # Save to output directory
    output_path = os.path.join(output_dir, "test_frame.jpg")
    try:
        with open(output_path, 'wb') as f:
            f.write(frame)
        logger.info(f"SUCCESS: Frame saved to {output_path}")
        logger.info(f"  Open this file to visually verify the stream is working")
        return True
    except Exception as e:
        logger.error(f"FAILED: Could not save frame: {e}")
        return False

def test_mjpeg_generator(url, num_frames=5):
    """Test 6: Test the MJPEG generator output"""
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"TEST 6: Testing MJPEG generator (capturing {num_frames} frames)...")
    logger.info("=" * 60)

    streamor = Streamor(url=url, logger=logger)
    streamor.start()

    # Give it time to capture first frame
    time.sleep(2)

    frames_yielded = 0
    total_bytes = 0

    try:
        for frame_data in streamor.generate():
            frames_yielded += 1
            total_bytes += len(frame_data)

            # Verify MJPEG boundary format
            if b'--OctoPrintStream' in frame_data:
                logger.info(f"  Frame {frames_yielded}: {len(frame_data)} bytes (valid boundary)")
            else:
                logger.warning(f"  Frame {frames_yielded}: {len(frame_data)} bytes (MISSING BOUNDARY!)")

            if frames_yielded >= num_frames:
                break

    finally:
        streamor.stop()

    if frames_yielded >= num_frames:
        logger.info(f"SUCCESS: Generator yielded {frames_yielded} frames")
        logger.info(f"  Total bytes: {total_bytes}")
        return True
    else:
        logger.error(f"FAILED: Only received {frames_yielded} of {num_frames} expected frames")
        return False

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nERROR: Please provide an RTSP URL or 'TEST' for test pattern mode")
        print("\nExample:")
        print("  python test_stream.py rtsp://admin:password@192.168.1.100:554/live")
        print("  python test_stream.py TEST")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = os.path.dirname(os.path.abspath(__file__))

    logger.info("=" * 60)
    logger.info("OctoPrint-RTSP Stream Diagnostics")
    logger.info("=" * 60)
    logger.info(f"Output directory: {output_dir}")
    logger.info("")

    results = {}

    # Run tests
    results['ffmpeg'] = check_ffmpeg()

    if not results['ffmpeg']:
        logger.error("\nCRITICAL: FFmpeg not available. Cannot continue.")
        sys.exit(1)

    results['rtsp_connection'] = test_rtsp_connection(url)

    results['raw_ffmpeg'] = test_raw_ffmpeg(url, output_dir)

    if not results['raw_ffmpeg']:
        logger.error("\nCRITICAL: Raw FFmpeg capture failed. The issue is with FFmpeg/RTSP, not Streamor.")
        logger.error("Check: 1) RTSP URL is correct  2) Camera is accessible  3) Credentials are right")
        # Continue anyway to see full diagnostics

    results['frame_capture'], streamor = test_frame_capture(url)

    if results['frame_capture']:
        # Need to restart for these tests since we stopped it
        streamor = Streamor(url=url, logger=logger)
        streamor.start()
        time.sleep(3)  # Let it capture some frames

        results['jpeg_valid'] = test_jpeg_validity(streamor)
        results['save_frame'] = save_test_frame(streamor, output_dir)
        streamor.stop()

        results['mjpeg_generator'] = test_mjpeg_generator(url)
    else:
        results['jpeg_valid'] = False
        results['save_frame'] = False
        results['mjpeg_generator'] = False

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    all_passed = True
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        symbol = "✓" if passed else "✗"
        logger.info(f"  [{symbol}] {test_name}: {status}")
        if not passed:
            all_passed = False

    logger.info("")
    if all_passed:
        logger.info("All tests PASSED! The stream should work in OctoPrint.")
        logger.info(f"Check the saved frame at: {os.path.join(output_dir, 'test_frame.jpg')}")
    else:
        logger.error("Some tests FAILED. Review the output above for details.")

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
