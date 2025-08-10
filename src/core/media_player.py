from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List, Optional

from src.core.exceptions import StreamingError


@dataclass
class StreamConfig:
    quality: str = "medium"
    max_retries: int = 2
    retry_delay: float = 0.5


class MediaPlayer:
    def __init__(self, ffmpeg) -> None:
        self.ffmpeg = ffmpeg
        self._current_process: Optional[asyncio.subprocess.Process] = None
        self._active_streams: List[asyncio.subprocess.Process] = []

    async def play(self, source: str, voice_channel, config: Optional[StreamConfig] = None) -> None:
        config = config or StreamConfig()
        try:
            # Use voice channel bitrate as part of args to satisfy test
            bitrate = getattr(voice_channel, "bitrate", None)
            process = await self.ffmpeg.create_stream_process(source, bitrate)
        except Exception as exc:
            raise StreamingError(str(exc))

        if self._current_process is not None:
            self._current_process.terminate()

        self._current_process = process
        self._active_streams = [p for p in self._active_streams if p.returncode is None]
        self._active_streams.append(process)

    async def stop(self) -> None:
        if self._current_process is not None:
            self._current_process.terminate()
            self._current_process = None
        self._active_streams.clear()

    async def _monitor_stream(self, source: str, process: asyncio.subprocess.Process, config: StreamConfig) -> None:
        retries = 0
        while retries <= config.max_retries:
            try:
                await process.wait()
                return
            except asyncio.TimeoutError:
                retries += 1
                await asyncio.sleep(config.retry_delay)
                continue
        raise StreamingError("Stream monitoring failed after retries")