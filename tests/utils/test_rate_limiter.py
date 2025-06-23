"""Tests for the rate limiter utility."""
import pytest
import asyncio
import time
from datetime import datetime, timedelta
from src.utils.rate_limiter import RateLimiter, GitHubRateLimiter, RateLimit


@pytest.mark.asyncio
async def test_rate_limiter_basic():
    """Test basic rate limiter functionality."""
    limiter = RateLimiter(calls_per_second=2.0, burst_size=2)

    # First two calls should be immediate
    start_time = time.time()
    await limiter.acquire()
    await limiter.acquire()
    duration = time.time() - start_time
    assert duration < 0.1  # Should be near-instant

    # Third call should wait
    start_time = time.time()
    await limiter.acquire()
    duration = time.time() - start_time
    assert 0.4 < duration < 0.6  # Should wait ~0.5 seconds


@pytest.mark.asyncio
async def test_rate_limiter_burst():
    """Test rate limiter burst handling."""
    limiter = RateLimiter(calls_per_second=1.0, burst_size=3)

    # Should allow burst of 3 calls
    start_time = time.time()
    for _ in range(3):
        await limiter.acquire()
    duration = time.time() - start_time
    assert duration < 0.1

    # Fourth call should wait
    await limiter.acquire()
    duration = time.time() - start_time
    assert duration >= 1.0


@pytest.mark.asyncio
async def test_rate_limiter_concurrent():
    """Test rate limiter with concurrent access."""
    limiter = RateLimiter(calls_per_second=5.0, burst_size=5)

    async def worker():
        await limiter.acquire()
        return time.time()

    # Launch 10 concurrent workers
    start_time = time.time()
    results = await asyncio.gather(*[worker() for _ in range(10)])

    # First 5 should be near-instant, rest should be spaced out
    assert all(t - start_time < 0.1 for t in results[:5])
    assert all(0.1 < t - start_time < 2.0 for t in results[5:])


@pytest.mark.asyncio
async def test_github_rate_limiter():
    """Test GitHub-specific rate limiter."""
    limiter = GitHubRateLimiter()

    # Update limits
    limiter.update_limits(category="core", remaining=10, reset_time=time.time() + 3600, limit=30)

    # Should allow calls when quota available
    assert await limiter.check_limit("core", required=5)

    # Update with low remaining
    limiter.update_limits(category="core", remaining=2, reset_time=time.time() + 3600, limit=30)

    # Should deny calls when insufficient quota
    assert not await limiter.check_limit("core", required=5)


@pytest.mark.asyncio
async def test_github_rate_limiter_reset():
    """Test GitHub rate limiter reset behavior."""
    limiter = GitHubRateLimiter()

    # Set limit with short reset time
    reset_time = time.time() + 1
    limiter.update_limits(category="search", remaining=0, reset_time=reset_time, limit=30)

    # Should deny calls before reset
    assert not await limiter.check_limit("search")

    # Wait for reset
    await asyncio.sleep(1.1)

    # Should allow calls after reset
    assert await limiter.check_limit("search")


@pytest.mark.asyncio
async def test_github_rate_limiter_categories():
    """Test GitHub rate limiter with different categories."""
    limiter = GitHubRateLimiter()

    # Set different limits for different categories
    limiter.update_limits("core", 1000, time.time() + 3600, 5000)
    limiter.update_limits("search", 10, time.time() + 3600, 30)

    # Core category should allow high-volume calls
    assert await limiter.check_limit("core", required=100)

    # Search category should be more restricted
    assert not await limiter.check_limit("search", required=20)


@pytest.mark.asyncio
async def test_github_rate_limiter_acquire():
    """Test GitHub rate limiter acquire method."""
    limiter = GitHubRateLimiter()

    # Set generous limits
    limiter.update_limits(
        category="core", remaining=1000, reset_time=time.time() + 3600, limit=5000
    )

    # Test successful acquire
    assert await limiter.acquire("core", required=1)

    # Test rate limiting
    start_time = time.time()
    await asyncio.gather(*[limiter.acquire("core") for _ in range(5)])
    duration = time.time() - start_time
    assert duration >= 4.0  # Should take at least 4 seconds due to rate limiting


def test_rate_limit_dataclass():
    """Test RateLimit dataclass functionality."""
    limit = RateLimit(remaining=100, reset_time=time.time() + 3600, limit=200)

    assert limit.remaining == 100
    assert limit.limit == 200
    assert limit.reset_time > time.time()
