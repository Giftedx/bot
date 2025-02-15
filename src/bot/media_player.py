import platform
import subprocess
from typing import Optional


class MediaPlayer:
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.system = platform.system().lower()

    def start(self, url: str) -> bool:
        """Start playing media URL in VLC"""
        try:
            # Kill existing process if any
            if self.process:
                self.stop()

            # Construct VLC command based on platform
            if self.system == "windows":
                vlc_path = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
            else:
                vlc_path = "vlc"

            # Start VLC in fullscreen mode
            self.process = subprocess.Popen(
                [vlc_path, "--fullscreen", "--no-video-title-show", url]
            )
            return True
        except FileNotFoundError:
            print("Error: VLC not found. Please install VLC media player.")
            return False
        except Exception as e:
            print(f"Error starting VLC: {e}")
            return False

    def pause(self) -> bool:
        """Pause/Resume playback"""
        try:
            if not self.process:
                return False

            if self.system == "windows":
                # Windows: Send space key using VBScript
                script = """
                Set WshShell = WScript.CreateObject("WScript.Shell")
                WshShell.AppActivate "VLC media player"
                WScript.Sleep 100
                WshShell.SendKeys " "
                """
                with open("pause_vlc.vbs", "w") as f:
                    f.write(script)
                subprocess.run(["cscript", "//nologo", "pause_vlc.vbs"])
            elif self.system == "darwin":
                # macOS: Use AppleScript
                subprocess.run(["osascript", "-e", 'tell application "VLC" to play'])
            else:
                # Linux: Use xdotool
                subprocess.run(["xdotool", "key", "space"])
            return True
        except Exception as e:
            print(f"Error pausing playback: {e}")
            return False

    def stop(self) -> None:
        """Stop playback and close VLC"""
        if self.process:
            self.process.terminate()
            self.process = None
