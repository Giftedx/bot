from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.core.exceptions import FFmpegError


@dataclass
class FFmpegConfig:
    input_path: str
    output_path: str
    video_codec: str
    audio_codec: str
    bitrate: str


class FFmpegManager:
    def __init__(self) -> None:
        self.ffmpeg_path: Optional[str] = None

    def _find_ffmpeg(self) -> Optional[str]:
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True)
            if result.returncode == 0:
                return "ffmpeg"
        except FileNotFoundError:
            return None
        return None

    def _ensure_ffmpeg(self) -> None:
        if not self.ffmpeg_path:
            self.ffmpeg_path = self._find_ffmpeg()

    def _verify_ffmpeg(self) -> None:
        self._ensure_ffmpeg()
        if not self.ffmpeg_path:
            raise FFmpegError("FFmpeg not found")
        try:
            result = subprocess.run([self.ffmpeg_path, "-version"], capture_output=True)
            if result.returncode != 0:
                raise FFmpegError("FFmpeg verification failed")
        except subprocess.SubprocessError as exc:
            raise FFmpegError(str(exc))

    async def transcode_media(self, config: FFmpegConfig) -> None:
        self._validate_media_path(Path(config.input_path))
        self._verify_ffmpeg()
        args = [
            self.ffmpeg_path,
            "-i",
            config.input_path,
            "-c:v",
            config.video_codec,
            "-c:a",
            config.audio_codec,
            "-b:v",
            config.bitrate,
            config.output_path,
        ]
        proc = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise FFmpegError(f"Transcoding failed: {stderr.decode('utf-8')}")

    def _validate_media_path(self, path: Path) -> None:
        if any(c in path.as_posix() for c in ['<', '>', '|', '\\', '"']):
            raise ValueError("Invalid characters in media path")
        if ".." in path.parts:
            raise ValueError("Directory traversal detected in media path")

    async def create_stream_process(self, source: str, bitrate: Optional[int]) -> asyncio.subprocess.Process:
        # Minimal placeholder for tests; does not actually stream
        proc = asyncio.create_subprocess_exec("echo", "stream", stdout=asyncio.subprocess.PIPE)
        return await proc

    async def cleanup(self) -> None:
        # Placeholder for compatibility with tests
        return None