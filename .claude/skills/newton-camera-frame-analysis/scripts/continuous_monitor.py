#!/usr/bin/env python3
"""Continuous monitoring script that captures and analyzes frames every 5 seconds."""

import sys
import os
import time
import signal
import argparse
from datetime import datetime
from pathlib import Path

sys.path.append('skills/activity-monitor-frame-query/scripts')
from webcam_analyze import capture_webcam_image, analyze_image

class ContinuousMonitor:
    def __init__(self, camera_index=0, output_dir="captures", interval=5, focus="Describe what you see"):
        self.camera_index = camera_index
        self.output_dir = output_dir
        self.interval = interval
        self.focus = focus
        self.running = True
        self.frame_count = 0

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        Path(output_dir).mkdir(exist_ok=True)

        self.api_key = os.environ.get("ATAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("ATAI_API_KEY environment variable not set")

    def signal_handler(self, signum, frame):
        print("\n\nStopping continuous monitoring...")
        self.running = False

    def run(self):
        """Run continuous monitoring loop."""
        print(f"Starting continuous monitoring (Ctrl+C to stop)")
        print(f"Camera: {self.camera_index}, Interval: {self.interval}s")
        print(f"Output directory: {self.output_dir}")
        print(f"Analysis focus: {self.focus}")
        print("-" * 60)

        while self.running:
            try:
                self.frame_count += 1
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[Frame {self.frame_count}] {timestamp}")

                image_path = capture_webcam_image(self.camera_index, self.output_dir)

                analyze_image(self.api_key, image_path, self.focus)

                if self.running:
                    print(f"Waiting {self.interval} seconds...")
                    time.sleep(self.interval)

            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                print(f"Error during capture/analysis: {e}")
                if self.running:
                    print(f"Retrying in {self.interval} seconds...")
                    time.sleep(self.interval)

        print(f"\nMonitoring complete. Captured {self.frame_count} frames.")
        print(f"Images saved in: {self.output_dir}/")


def main():
    parser = argparse.ArgumentParser(
        description="Continuously capture and analyze webcam frames at regular intervals"
    )
    parser.add_argument(
        "focus",
        nargs="?",
        default="Describe what you see and any changes from the previous frame",
        help="Question or focus for analysis (default: describe changes)"
    )
    parser.add_argument(
        "--camera", "-c",
        type=int,
        default=0,
        help="Camera index (0 for built-in, 1+ for external)"
    )
    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=5.0,
        help="Capture interval in seconds (default: 5)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="captures",
        help="Directory for saved captures (default: captures)"
    )

    args = parser.parse_args()

    monitor = ContinuousMonitor(
        camera_index=args.camera,
        output_dir=args.output_dir,
        interval=args.interval,
        focus=args.focus
    )

    try:
        monitor.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())