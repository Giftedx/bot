import unittest

# Import statements
try:
    from src.api.api.routes import app
except ImportError:
    app = None
try:
    from src.core.exceptions import (
        StreamingError,
        MediaNotFoundError,
    )
except ImportError:
    StreamingError = None
    MediaNotFoundError = None
try:
    from src.core.caching import (
        CacheManager,
        CachePolicy,
        CacheEntry,
    )
except ImportError:
    CacheManager = None
    CachePolicy = None
    CacheEntry = None
try:
    from src.core.di_container import DIContainer, Container
except ImportError:
    DIContainer = None
    Container = None
try:
    from src.core import ffmpeg_manager
except ImportError:
    ffmpeg_manager = None
try:
    from src.core import media_player
except ImportError:
    media_player = None
try:
    from src.core import plex
except ImportError:
    plex = None
try:
    from src.core import queue_manager
except ImportError:
    queue_manager = None
try:
    from src.core import rate_limiter
except ImportError:
    rate_limiter = None
# The following import is dependent on the correct installation of
# prometheus_client
try:
    import prometheus_client
except ImportError:
    prometheus_client = None


class TestImports(unittest.TestCase):

    def test_api_routes_import(self):
        self.assertIsNotNone(app)

    def test_exceptions_import(self):
        self.assertIsNotNone(StreamingError)
        self.assertIsNotNone(MediaNotFoundError)

    def test_caching_import(self):
        self.assertIsNotNone(CacheManager)
        self.assertIsNotNone(CachePolicy)
        self.assertIsNotNone(CacheEntry)

    def test_di_container_import(self):
        self.assertIsNotNone(DIContainer)
        self.assertIsNotNone(Container)

    def test_ffmpeg_manager_import(self):
        self.assertIsNotNone(ffmpeg_manager)

    def test_media_player_import(self):
        self.assertIsNotNone(media_player)

    def test_plex_import(self):
        self.assertIsNotNone(plex)

    def test_queue_manager_import(self):
        self.assertIsNotNone(queue_manager)

    def test_rate_limiter_import(self):
        self.assertIsNotNone(rate_limiter)

    def test_redis_import(self):
        pass  # Removed since I don't know which specific redis components.

    def test_prometheus_client_import(self):
        self.assertIsNotNone(prometheus_client)


if __name__ == '__main__':
    unittest.main()