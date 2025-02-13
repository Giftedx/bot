import sys
import os
import pytest
from unittest.mock import Mock
# Keep PlexManager import
from src.core.plex_manager import PlexManager 
from src.core.exceptions import StreamingError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))


@pytest.fixture
def mock_process():
    process = Mock()
    process.returncode = 0
    process.communicate = Mock(return_value=(b"", b""))
    process.wait = Mock()
    return process
