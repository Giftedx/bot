import asyncio
from typing import Any, AsyncGenerator
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import subprocess
import platform
from pathlib import Path

from src.core.ffmpeg_manager import FFmpegManager, FFmpegConfig
from src.core.exceptions import StreamingError, FFmpegError
from src.monitoring.metrics import METRICS


@pytest.fixture
async def ffmpeg_manager() -> AsyncGenerator[FFmpegManager, None]:
    manager = FFmpegManager()
    yield manager
    await manager.cleanup()


def test_ffmpeg_config_dataclass() -> None:
    """Test FFmpeg configuration dataclass."""
    config = FFmpegConfig(
        input_path="test.mp4",
        output_path="output.mp4",
        video_codec="h264",
        audio_codec="aac",
        bitrate="2M",
    )
    assert config.input_path == "test.mp4"
    assert config.video_codec == "h264"


@patch("subprocess.run")
def test_find_ffmpeg_success(mock_run: MagicMock) -> None:
    """Test successful FFmpeg binary location."""
    mock_run.return_value.returncode = 0
    ffmpeg_path = FFmpegManager()._find_ffmpeg()
    assert ffmpeg_path is not None
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_find_ffmpeg_failure(mock_run: MagicMock) -> None:
    """Test FFmpeg binary not found scenario."""
    mock_run.side_effect = FileNotFoundError("FFmpeg not found")
    with pytest.raises(FFmpegError) as exc_info:
        FFmpegManager()
    assert "FFmpeg not found" in str(exc_info.value)


@patch("src.core.ffmpeg_manager.FFmpegManager._find_ffmpeg", return_value="fake_path")
def test_verify_ffmpeg_success(mock_find_ffmpeg: MagicMock, ffmpeg_manager: FFmpegManager) -> None:
    """Test FFmpeg verification success."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        ffmpeg_manager._verify_ffmpeg()


@patch("src.core.ffmpeg_manager.FFmpegManager._find_ffmpeg", return_value="fake_path")
def test_verify_ffmpeg_failure(mock_find_ffmpeg: MagicMock, ffmpeg_manager: FFmpegManager) -> None:
    """Test FFmpeg verification failure."""
    with patch(
        "subprocess.run", side_effect=subprocess.SubprocessError("FFmpeg verification failed")
    ):
        with pytest.raises(FFmpegError) as exc_info:
            ffmpeg_manager._verify_ffmpeg()
        assert "verification failed" in str(exc_info.value).lower()


@pytest.mark.asyncio
@patch("src.core.ffmpeg_manager.FFmpegManager._find_ffmpeg", return_value="fake_path")
async def test_transcode_media_success(
    mock_find_ffmpeg: MagicMock, ffmpeg_manager: FFmpegManager
) -> None:
    """Test successful media transcoding."""
    config = FFmpegConfig(
        input_path="test.mp4",
        output_path="output.mp4",
        video_codec="h264",
        audio_codec="aac",
        bitrate="2M",
    )

    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = (b"", b"")

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        await ffmpeg_manager.transcode_media(config)
        mock_process.communicate.assert_called_once()


@pytest.mark.asyncio
@patch("src.core.ffmpeg_manager.FFmpegManager._find_ffmpeg", return_value="fake_path")
async def test_transcode_media_failure(
    mock_find_ffmpeg: MagicMock, ffmpeg_manager: FFmpegManager
) -> None:
    """Test media transcoding failure."""
    config = FFmpegConfig(
        input_path="test.mp4",
        output_path="output.mp4",
        video_codec="h264",
        audio_codec="aac",
        bitrate="2M",
    )

    mock_process = AsyncMock()
    mock_process.returncode = 1
    mock_process.communicate.return_value = (b"", b"FFmpeg error output")

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        with pytest.raises(FFmpegError) as exc_info:
            await ffmpeg_manager.transcode_media(config)
        assert "transcoding failed" in str(exc_info.value).lower()


def test_validate_media_path_valid(ffmpeg_manager: FFmpegManager) -> None:
    """Test valid media path validation."""
    valid_path = Path("test.mp4")
    assert ffmpeg_manager._validate_media_path(valid_path) is None


def test_validate_media_path_invalid_chars(ffmpeg_manager: FFmpegManager) -> None:
    """Test invalid media path characters."""
    invalid_path = Path("test<>.mp4")
    with pytest.raises(ValueError) as exc_info:
        ffmpeg_manager._validate_media_path(invalid_path)
    assert "invalid characters" in str(exc_info.value).lower()


def test_validate_media_path_directory_traversal(ffmpeg_manager: FFmpegManager) -> None:
    """Test directory traversal prevention."""
    traversal_path = Path("../test.mp4")
    with pytest.raises(ValueError) as exc_info:
        ffmpeg_manager._validate_media_path(traversal_path)
    assert "directory traversal" in str(exc_info.value).lower()
