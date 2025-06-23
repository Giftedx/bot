import pytest
import asyncio
from typing import AsyncGenerator, Any
from unittest.mock import patch, AsyncMock, Mock
from redis.exceptions import RedisError
from src.utils.redis_manager import RedisManager, RedisKeys
from src.core.exceptions import RedisConnectionError, RedisOperationError
from src.core.settings_manager import SettingsManager
from asynctest import IsolatedAsyncioTestCase
from datetime import datetime, timedelta


@pytest.fixture
def settings():
    settings_mock = Mock(spec=SettingsManager)
    settings_mock.redis_url = "redis://localhost:6379/0"
    settings_mock.redis_max_connections = 10
    return settings_mock


@pytest.fixture
async def redis_manager(mocker: Any) -> AsyncGenerator[RedisManager, None]:
    settings = Mock(spec=SettingsManager)
    settings.redis_host = "localhost"
    settings.redis_port = 6379
    settings.redis_db = 0

    manager = RedisManager(settings)
    yield manager
    await manager.close()


@pytest.mark.asyncio
async def test_connection_success(redis_manager: RedisManager, mocker: Any) -> None:
    mock_redis = AsyncMock()
    mocker.patch("redis.asyncio.Redis", return_value=mock_redis)

    async with redis_manager.get_connection() as conn:
        assert conn is not None
        mock_redis.ping.assert_called_once()


@pytest.mark.asyncio
async def test_connection_failure(redis_manager: RedisManager, mocker: Any) -> None:
    mock_redis = AsyncMock()
    mock_redis.ping.side_effect = RedisError("Connection failed")
    mocker.patch("redis.asyncio.Redis", return_value=mock_redis)

    with pytest.raises(RedisConnectionError) as exc_info:
        async with redis_manager.get_connection():
            pass
    assert "Connection failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_operation_error(redis_manager: RedisManager, mocker: Any) -> None:
    mock_redis = AsyncMock()
    mock_redis.get.side_effect = RedisError("Operation failed")
    mocker.patch("redis.asyncio.Redis", return_value=mock_redis)

    with pytest.raises(RedisOperationError) as exc_info:
        async with redis_manager.get_connection() as conn:
            await conn.get("test_key")
    assert "Operation failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_connection_cleanup(redis_manager: RedisManager) -> None:
    async with redis_manager.get_connection():
        assert redis_manager._redis is not None
        assert redis_manager.pool is not None

    await redis_manager.close()
    assert redis_manager._redis is None
    assert redis_manager.pool is None


@pytest.mark.asyncio
async def test_retry_operation_success(redis_manager: RedisManager, mocker: Any) -> None:
    operation = AsyncMock()
    operation.side_effect = [RedisError(), RedisError(), "success"]

    result = await redis_manager._retry_operation(operation, "test_arg")
    assert result == "success"
    assert operation.call_count == 3


@pytest.mark.asyncio
async def test_retry_operation_failure(redis_manager: RedisManager, mocker: Any) -> None:
    operation = AsyncMock()
    operation.side_effect = RedisError("Persistent failure")

    with pytest.raises(RedisOperationError) as exc_info:
        await redis_manager._retry_operation(operation, "test_arg")
    assert "Persistent failure" in str(exc_info.value)
    assert operation.call_count == redis_manager.MAX_RETRIES


@pytest.mark.asyncio
async def test_publish_message(redis_manager, mocker):
    mock_redis = AsyncMock()
    mocker.patch("redis.asyncio.Redis", return_value=mock_redis)

    message = {"type": "test", "data": "value"}
    await redis_manager.publish("test_channel", message)

    mock_redis.publish.assert_called_once()
    assert "media:events:test_channel" in mock_redis.publish.call_args[0]


@pytest.mark.asyncio
async def test_subscribe_receive_message(redis_manager, mocker):
    mock_redis = AsyncMock()
    mock_pubsub = AsyncMock()
    mock_pubsub.get_message.side_effect = [{"data": '{"type": "test", "value": 1}'}, None]
    mock_redis.pubsub.return_value = mock_pubsub
    mocker.patch("redis.asyncio.Redis", return_value=mock_redis)

    async with redis_manager.subscribe("test_channel") as messages:
        async for message in messages:
            assert message["type"] == "test"
            break


@pytest.mark.asyncio
async def test_cache_operations(redis_manager, mocker):
    mock_redis = AsyncMock()
    mocker.patch("redis.asyncio.Redis", return_value=mock_redis)

    test_data = {"key": "value"}
    await redis_manager.cache_set("test_key", test_data)
    cached_data = await redis_manager.cache_get("test_key")

    assert cached_data == test_data


@pytest.mark.asyncio
async def test_cached_decorator(redis_manager, mocker):
    mock_redis = AsyncMock()
    mocker.patch("redis.asyncio.Redis", return_value=mock_redis)

    @redis_manager.cached()
    async def test_func():
        return "test_result"

    result1 = await test_func()
    result2 = await test_func()

    assert result1 == result2 == "test_result"
    assert mock_redis.get.called


@pytest.mark.asyncio
async def test_leaderboard_operations(redis_manager, mocker):
    mock_redis = AsyncMock()
    mocker.patch("redis.asyncio.Redis", return_value=mock_redis)

    await redis_manager.leaderboard_add("game", "player1", 100)
    await redis_manager.leaderboard_add("game", "player2", 200)

    leaderboard = await redis_manager.leaderboard_get_range("game", 0, -1)
    assert len(leaderboard) == 2
    assert leaderboard[0][0] == "player2"  # Highest score first


@pytest.mark.asyncio
async def test_rate_limit_not_exceeded(redis_manager, mocker):
    mock_redis = AsyncMock()
    mock_pipeline = AsyncMock()
    mock_redis.pipeline.return_value = mock_pipeline
    mock_pipeline.execute.return_value = [1, 1, 5, 1]  # Sample pipeline results
    mocker.patch("redis.asyncio.Redis", return_value=mock_redis)

    result = await redis_manager.check_rate_limit("api", "user1", 10, 60)
    assert result is True


@pytest.mark.asyncio
async def test_rate_limit_exceeded(redis_manager, mocker):
    mock_redis = AsyncMock()
    mock_pipeline = AsyncMock()
    mock_redis.pipeline.return_value = mock_pipeline
    mock_pipeline.execute.return_value = [1, 1, 11, 1]  # Over limit
    mocker.patch("redis.asyncio.Redis", return_value=mock_redis)

    with pytest.raises(RedisRateLimitExceededError):
        await redis_manager.check_rate_limit("api", "user1", 10, 60)


@pytest.mark.asyncio
async def test_stream_add(redis_manager, mocker):
    mock_redis = AsyncMock()
    mock_redis.xadd.return_value = "1234567890-0"
    mocker.patch("redis.asyncio.Redis", return_value=mock_redis)

    message_id = await redis_manager.stream_add("test_stream", {"key": "value"})
    assert message_id == "1234567890-0"
    mock_redis.xadd.assert_called_once()


@pytest.mark.asyncio
async def test_create_consumer_group(redis_manager, mocker):
    mock_redis = AsyncMock()
    mocker.patch("redis.asyncio.Redis", return_value=mock_redis)

    await redis_manager.create_consumer_group("test_stream", "test_group")
    mock_redis.xgroup_create.assert_called_once()


@pytest.mark.asyncio
async def test_stream_read(redis_manager, mocker):
    mock_redis = AsyncMock()
    mock_redis.xread.return_value = [("test_stream", [("1234567890-0", {"key": "value"})])]
    mocker.patch("redis.asyncio.Redis", return_value=mock_redis)

    messages = await redis_manager.stream_read("test_stream")
    assert len(messages) == 1
    assert messages[0][1][0][1]["key"] == "value"


@pytest.mark.asyncio
async def test_stream_read_group(redis_manager, mocker):
    mock_redis = AsyncMock()
    mock_redis.xreadgroup.return_value = [("test_stream", [("1234567890-0", {"key": "value"})])]
    mocker.patch("redis.asyncio.Redis", return_value=mock_redis)

    messages = await redis_manager.stream_read_group("test_stream", "test_group", "consumer1")
    assert len(messages) == 1
    assert messages[0][1][0][1]["key"] == "value"


class TestRedisManager(IsolatedAsyncioTestCase):
    """
    Tests for the RedisManager class.
    """

    async def test_add_to_queue(self, redis_manager):
        """
        Test adding an item to the queue.
        """
        item = "test_item"
        await redis_manager.add_to_queue(item)
        redis_manager.redis.rpush.assert_called_once_with(redis_manager.keys.queue_key, item)

    async def test_get_queue_length(self, redis_manager):
        """
        Test getting the queue length.
        """
        redis_manager.redis.llen.return_value = 5
        length = await redis_manager.get_queue_length()
        self.assertEqual(length, 5)
        redis_manager.redis.llen.assert_called_once_with(redis_manager.keys.queue_key)

    async def test_get_from_queue(self, redis_manager):
        """
        Test getting an item from the queue.
        """
        redis_manager.redis.blpop.return_value = [b"queue", b"test_item"]
        item = await redis_manager.get_from_queue()
        self.assertEqual(item, "test_item")
        redis_manager.redis.blpop.assert_called_once_with(redis_manager.keys.queue_key, timeout=0)

    async def test_get_from_queue_timeout(self, redis_manager):
        """
        Test getting an item from the queue with a timeout.
        """
        redis_manager.redis.blpop.return_value = None
        item = await redis_manager.get_from_queue(timeout=10)
        self.assertIsNone(item)
        redis_manager.redis.blpop.assert_called_once_with(redis_manager.keys.queue_key, timeout=10)

    async def test_queue_iterator(self, redis_manager):
        """
        Test the queue iterator.
        """
        redis_manager.redis.blpop.side_effect = [[b"queue", b"item1"], [b"queue", b"item2"], None]
        items = []
        async for batch in redis_manager.queue_iterator(batch_size=1):
            items.extend(batch)
        self.assertEqual(items, ["item1", "item2"])

    async def test_clear_queue(self, redis_manager):
        """
        Test clearing the queue.
        """
        await redis_manager.clear_queue()
        redis_manager.redis.delete.assert_called_once_with(redis_manager.keys.queue_key)

    async def test_get_all_items(self, redis_manager):
        """
        Test getting all items from the queue.
        """
        redis_manager.redis.llen.return_value = 2
        redis_manager.redis.lrange.return_value = [b"item1", b"item2"]
        items = await redis_manager.get_all_items()
        self.assertEqual(items, ["item1", "item2"])
        redis_manager.redis.llen.assert_called_once_with(redis_manager.keys.queue_key)
        redis_manager.redis.lrange.assert_called_once_with(redis_manager.keys.queue_key, 0, 1)

    async def test_close(self, redis_manager):
        """
        Test closing the Redis connection.
        """
        await redis_manager.close()
        redis_manager.redis.close.assert_called_once()
