import platform
import subprocess
from abc import ABC, abstractmethod
from typing import Optional

import cv2
import pyvirtualcam


class VirtualCameraBase(ABC):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def send_frame(self, frame):
        pass

    @abstractmethod
    def stop(self):
        pass


class WindowsVirtualCamera(VirtualCameraBase):
    def __init__(self, width: int = 1280, height: int = 720):
        self.width = width
        self.height = height
        self.cam: Optional[pyvirtualcam.Camera] = None

    def start(self):
        """Start virtual camera using OBS Virtual Camera"""
        self.cam = pyvirtualcam.Camera(
            width=self.width, height=self.height, fps=30, device="OBS Virtual Camera"
        )

    def send_frame(self, frame):
        """Send frame to virtual camera"""
        if self.cam:
            # Ensure frame is in RGB format
            if len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            elif frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)

            # Resize frame if needed
            if frame.shape[:2] != (self.height, self.width):
                frame = cv2.resize(frame, (self.width, self.height))

            self.cam.send(frame)
            self.cam.sleep_until_next_frame()

    def stop(self):
        """Stop virtual camera"""
        if self.cam:
            self.cam.close()
            self.cam = None


class LinuxVirtualCamera(VirtualCameraBase):
    def __init__(self, width: int = 1280, height: int = 720):
        self.width = width
        self.height = height
        self.device = "/dev/video0"
        self.process = None

    def start(self):
        """Start v4l2loopback device"""
        try:
            subprocess.run(["sudo", "modprobe", "v4l2loopback"])
            self.process = subprocess.Popen(
                [
                    "ffmpeg",
                    "-f",
                    "rawvideo",
                    "-pixel_format",
                    "rgb24",
                    "-video_size",
                    f"{self.width}x{self.height}",
                    "-framerate",
                    "30",
                    "-i",
                    "-",
                    "-f",
                    "v4l2",
                    "-pix_fmt",
                    "yuv420p",
                    self.device,
                ],
                stdin=subprocess.PIPE,
            )
        except Exception as e:
            print(f"Error starting virtual camera: {e}")
            self.process = None

    def send_frame(self, frame):
        """Send frame to virtual camera"""
        if self.process:
            try:
                self.process.stdin.write(frame.tobytes())
            except Exception as e:
                print(f"Error sending frame: {e}")

    def stop(self):
        """Stop virtual camera"""
        if self.process:
            self.process.terminate()
            self.process = None


def get_virtual_camera():
    """Get appropriate virtual camera implementation for current platform"""
    system = platform.system().lower()
    if system == "windows":
        return WindowsVirtualCamera()
    elif system == "linux":
        return LinuxVirtualCamera()
    else:
        raise NotImplementedError(f"Virtual camera not implemented for {system}")
