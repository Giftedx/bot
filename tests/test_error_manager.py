import pytest

from src.core.error_manager import ErrorManager


async def unstable(value: int):
    if unstable.attempts < 2:
        unstable.attempts += 1
        raise ValueError("fail")
    return value


unstable.attempts = 0


@ErrorManager.retry_on_error(max_retries=3, exceptions=(ValueError,))
async def wrapped(value: int):
    return await unstable(value)


@pytest.mark.asyncio
async def test_retry_on_error():
    unstable.attempts = 0
    res = await wrapped(5)
    assert res == 5
    # Ensure function retried
    assert unstable.attempts == 2 