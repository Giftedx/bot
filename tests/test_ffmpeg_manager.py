import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import subprocess
import platform

from src.core.ffmpeg_manager import FFmpegManager, FFmpegConfig
from src.core.exceptions import StreamingError, FFmpegError # Import FFmpegError
from src.monitoring.metrics import METRICS

@pytest.fixture
def ffmpeg_manager():
    with patch("src.core.ffmpeg_manager.FFmpegManager._find_ffmpeg", return_value="fake_path"), \
         patch("subprocess.run") as mock_subprocess_run: # Patch subprocess.run and assign to mock_subprocess_run
        mock_subprocess_run.return_value.returncode = 0 # Default return code for subprocess.run
        manager = FFmpegManager() # Initialize FFmpegManager with mocks in place
    return manager

def test_ffmpeg_config_dataclass():
    config = FFmpegConfig()
    assert config.thread_queue_size == 512
    assert config.hwaccel == "auto"
    assert config.preset == "veryfast"
    assert config.width == 1280
    assert config.height == 720
    assert config.audio_bitrate == "192k"
    assert config.video_bitrate == "3000k"
    assert config.threads == 4

def test_find_ffmpeg_success():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        ffmpeg_path = FFmpegManager()._find_ffmpeg()
        assert ffmpeg_path is not None

def test_find_ffmpeg_failure():
    with patch('subprocess.run', side_effect=FileNotFoundError):
        with pytest.raises(FFmpegError): # Changed expected exception to FFmpegError
            FFmpegManager()

@patch("src.core.ffmpeg_manager.FFmpegManager._find_ffmpeg", return_value="fake_path")
def test_verify_ffmpeg_success(mock_find_ffmpeg, ffmpeg_manager):
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        ffmpeg_manager._verify_ffmpeg()
        assert True # No exception raised

@patch("src.core.ffmpeg_manager.FFmpegManager._find_ffmpeg", return_value="fake_path")
def test_verify_ffmpeg_failure(mock_find_ffmpeg, ffmpeg_manager):
    with patch('subprocess.run', side_effect=subprocess.SubprocessError):
        with pytest.raises(FFmpegError): # Changed expected exception to FFmpegError
            ffmpeg_manager._verify_ffmpeg()

@patch("src.core.ffmpeg_manager.FFmpegManager._find_ffmpeg", return_value="fake_path")
def test_check_hwaccel_timeout(mock_find_ffmpeg, ffmpeg_manager):
    with patch('subprocess.run', side_effect=subprocess.TimeoutExpired):
        with pytest.raises(FFmpegError) as exc_info:
            ffmpeg_manager._check_hwaccel()
        assert "FFmpeg hardware acceleration check timed out." in str(exc_info.value)

@patch("src.core.ffmpeg_manager.FFmpegManager._find_ffmpeg", return_value="fake_path")
def test_check_hwaccel_failure(mock_find_ffmpeg, ffmpeg_manager):
    with patch('subprocess.run', side_effect=subprocess.SubprocessError("HWAccel check failed")):
        with pytest.raises(FFmpegError) as exc_info:
            ffmpeg_manager._check_hwaccel()
        assert "FFmpeg hardware acceleration check failed" in str(exc_info.value)

@patch("src.core.ffmpeg_manager.FFmpegManager.get_stream_options")
def test_transcode_media_success(mock_get_stream_options, ffmpeg_manager):
    mock_get_stream_options.return_value = {"before_options": "", "options": ""}
    with patch('subprocess.Popen') as mock_popen:
        process = mock_popen.return_value
        process.communicate.return_value = (b"", b"") # Return byte strings
        process.returncode = 0

        ffmpeg_manager.transcode_media("input.mp4", "output.mp4")
        mock_popen.assert_called_once()

@patch("src.core.ffmpeg_manager.FFmpegManager.get_stream_options")
def test_transcode_media_failure(mock_get_stream_options, ffmpeg_manager):
    mock_get_stream_options.return_value = {"before_options": "", "options": ""}
    with patch('subprocess.Popen') as mock_popen:
        process = mock_popen.return_value
        process.communicate.return_value = (b"", b"FFmpeg error output") # Return byte strings
        process.returncode = 1

        with pytest.raises(FFmpegError) as exc_info:
            ffmpeg_manager.transcode_media("input.mp4", "output.mp4")
        assert "FFmpeg process exited unexpectedly" in str(exc_info.value)
        assert "Stderr: FFmpeg error output" in str(exc_info.value) # Check stderr in exception

@patch("src.core.ffmpeg_manager.FFmpegManager.get_stream_options")
def test_transcode_media_timeout(mock_get_stream_options, ffmpeg_manager):
    mock_get_stream_options.return_value = {"before_options": "", "options": ""}
    with patch('subprocess.Popen') as mock_popen:
        mock_popen_instance = mock_popen.return_value
        mock_popen_instance.communicate.side_effect = subprocess.TimeoutExpired(cmd="ffmpeg ...", timeout=10)

        with pytest.raises(FFmpegError) as exc_info:
            ffmpeg_manager.transcode_media("input.mp4", "output.mp4")
        assert "FFmpeg process timed out after 10 seconds." in str(exc_info.value)


@pytest.mark.asyncio
async def test_start_process_with_limits_file_not_found(ffmpeg_manager):
    command = ["ffmpeg", "-i", "input.mp4", "output.flv"]
    cmd_str = "ffmpeg -i input.mp4 output.flv"
    stream_id = "test_stream"
    with patch('asyncio.create_subprocess_exec', side_effect=FileNotFoundError("FFmpeg not found")):
        with pytest.raises(FFmpegError) as exc_info:
            await ffmpeg_manager._start_process_with_limits(command, cmd_str, stream_id)
        assert "FFmpeg executable not found" in str(exc_info.value)

@pytest.mark.asyncio
async def test_start_process_with_limits_os_error(ffmpeg_manager):
    command = ["ffmpeg", "-i", "input.mp4", "output.flv"]
    cmd_str = "ffmpeg -i input.mp4 output.flv"
    stream_id = "test_stream"
    with patch('asyncio.create_subprocess_exec', side_effect=OSError("OS Error")):
        with pytest.raises(FFmpegError) as exc_info:
            await ffmpeg_manager._start_process_with_limits(command, cmd_str, stream_id)
        assert "FFmpeg process creation failed" in str(exc_info.value)

@pytest.mark.asyncio
async def test_start_process_with_limits_timeout_error(ffmpeg_manager):
    command = ["ffmpeg", "-i", "input.mp4", "output.flv"]
    cmd_str = "ffmpeg -i input.mp4 output.flv"
    stream_id = "test_stream"
    with patch('asyncio.create_subprocess_exec', side_effect=TimeoutError("Timeout Error")):
        with pytest.raises(FFmpegError) as exc_info:
            await ffmpeg_manager._start_process_with_limits(command, cmd_str, stream_id)
        assert "FFmpeg process creation timed out" in str(exc_info.value)


@pytest.mark.asyncio
async def test_stream_media_success(ffmpeg_manager):
    with patch('asyncio.create_subprocess_exec') as mock_subprocess_exec:
        mock_subprocess_exec.return_value = AsyncMock()
        async with ffmpeg_manager.start_stream("input.mp4", "rtmp://test/url", "stream_key"): # Changed to start_stream
            mock_subprocess_exec.assert_called_once()

@pytest.mark.asyncio
async def test_stream_media_failure(ffmpeg_manager):
    with patch('asyncio.create_subprocess_exec') as mock_subprocess_exec:
        mock_subprocess_exec.side_effect = OSError("Failed to start")
        with pytest.raises(StreamingError):
            async with ffmpeg_manager.start_stream("input.mp4", "rtmp://test/url", "stream_key"): # Changed to start_stream
                pass

@pytest.mark.asyncio
async def test_stop_stream_success(ffmpeg_manager):
    mock_process = AsyncMock()
    ffmpeg_manager._active_processes["test_stream"] = mock_process
    await ffmpeg_manager.shutdown() # Changed to shutdown - to test cleanup logic
    mock_process.terminate.assert_called_once() # Changed to terminate as used in cleanup
    mock_process.kill.assert_not_called()

@pytest.mark.asyncio
async def test_stop_stream_forceful_kill(ffmpeg_manager):
    mock_process = AsyncMock()
    mock_process.wait.side_effect = asyncio.TimeoutError() # Simulate timeout
    ffmpeg_manager._active_processes["test_stream"] = mock_process
    await ffmpeg_manager.shutdown() # Changed to shutdown - to test cleanup logic
    mock_process.terminate.assert_called_once() # Terminate is called first in cleanup
    mock_process.kill.assert_called_once() # Kill is called on timeout


@pytest.mark.asyncio
async def test_cleanup(ffmpeg_manager):
    mock_process_1 = AsyncMock()
    mock_process_2 = AsyncMock()
    ffmpeg_manager._active_processes["stream1"] = mock_process_1
    ffmpeg_manager._active_processes["stream2"] = mock_process_2
    await ffmpeg_manager.shutdown() # Changed to shutdown - to test cleanup logic
    assert not ffmpeg_manager._active_processes
    mock_process_1.terminate.assert_called_once()
    mock_process_2.terminate.assert_called_once()

@pytest.mark.asyncio
async def test_concurrent_streams(ffmpeg_manager):
    with patch('asyncio.create_subprocess_exec') as mock_subprocess_exec:
        mock_subprocess_exec.return_value = AsyncMock()
        async with asyncio.TaskGroup() as tg:
            tg.create_task(ffmpeg_manager.start_stream("input1.mp4", "rtmp://test/url", "stream_key")) # Changed to start_stream
            tg.create_task(ffmpeg_manager.start_stream("input2.mp4", "rtmp://test/url", "stream_key")) # Changed to start_stream
        assert len(ffmpeg_manager._active_processes) == 2

@pytest.mark.asyncio
async def test_resource_monitoring(ffmpeg_manager):
    with patch('psutil.Process') as mock_psutil_process:
        mock_psutil_process.return_value.cpu_percent.return_value = 50.0
        mock_psutil_process.return_value.memory_info.return_value.rss = 500 * 1024 * 1024 # 500MB
        stats = await ffmpeg_manager.get_process_stats() # Changed to get_process_stats (public method)
        assert stats['cpu_total'] > 0
        assert stats['memory_total'] > 0
        assert stats['process_count'] == 0 # No active processes in this test

def test_get_stream_options(ffmpeg_manager):
    options = ffmpeg_manager.get_stream_options(
        width=1280,
        height=720,
        preset="veryfast",
        hwaccel="auto"
    )
    assert options is not None
    assert "-vf scale=1280:720" in options["options"]
    assert "-preset veryfast" in options["options"]
    assert "-hwaccel auto" in options["before_options"]

def test_validate_media_path_valid():
    FFmpegManager._validate_media_path("valid_path.mp4", "valid_path.mp4")
    FFmpegManager._validate_media_path("valid-path_123.mp4", "valid-path_123.mp4")
    FFmpegManager._validate_media_path("valid.path/to/media.mp4", "valid.path/to/media.mp4")
    assert True # No exception raised for valid paths

def test_validate_media_path_invalid_chars():
    with pytest.raises(StreamingError) as exc_info:
        FFmpegManager._validate_media_path("invalid*path.mp4", "invalid*path.mp4")
    assert "Invalid media path" in str(exc_info.value)

def test_validate_media_path_directory_traversal():
    with pytest.raises(StreamingError) as exc_info:
        FFmpegManager._validate_media_path("../../../../../etc/passwd", "../../../../../etc/passwd")
    assert "Invalid media path" in str(exc_info.value)
