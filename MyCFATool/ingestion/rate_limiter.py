import time
import logging
from typing import Optional
import redis


class RedisRateLimiter:
    """
    Distributed rate limiter using Redis sorted sets for sliding window rate limiting.

    This implementation uses Redis sorted sets to track API requests within a time window,
    allowing for distributed rate limiting across multiple instances.
    """

    def __init__(self, redis_client: redis.Redis, key_prefix: str = "fmp", limit: int = 120, window: int = 60):
        """
        Initialize the Redis rate limiter.

        Args:
            redis_client: Redis client instance
            key_prefix: Prefix for Redis keys
            limit: Maximum requests per time window
            window: Time window in seconds (default 60 for per minute)
        """
        self.redis = redis_client
        self.prefix = key_prefix
        self.limit = limit
        self.window = window
        self.logger = logging.getLogger(__name__)

    def allow_request(self, identifier: str = "default") -> bool:
        """
        Check if a request is allowed under the rate limit.

        Args:
            identifier: Unique identifier for the rate limit scope (e.g., API key or user)

        Returns:
            bool: True if request is allowed, False if rate limit exceeded
        """
        key = f"{self.prefix}:{identifier}"
        now = time.time()
        window_start = now - self.window

        try:
            # Remove requests older than the window
            self.redis.zremrangebyscore(key, '-inf', window_start)

            # Get current count
            count = self.redis.zcard(key)

            if count >= self.limit:
                self.logger.warning(f"Rate limit exceeded for {identifier}: {count}/{self.limit}")
                return False

            # Add new request timestamp
            self.redis.zadd(key, {str(now): now})
            # Set expiration on the key to clean up old keys
            self.redis.expire(key, self.window)

            self.logger.debug(f"Request allowed for {identifier}: {count + 1}/{self.limit}")
            return True

        except redis.RedisError as e:
            # If Redis fails, allow the request to avoid blocking the service
            self.logger.error(f"Redis error in rate limiter: {e}. Allowing request.")
            return True

    def get_remaining_requests(self, identifier: str = "default") -> int:
        """
        Get the number of remaining requests allowed in the current window.

        Args:
            identifier: Unique identifier for the rate limit scope

        Returns:
            int: Number of remaining requests
        """
        key = f"{self.prefix}:{identifier}"
        now = time.time()
        window_start = now - self.window

        try:
            self.redis.zremrangebyscore(key, '-inf', window_start)
            count = self.redis.zcard(key)
            remaining = max(0, self.limit - count)
            return remaining
        except redis.RedisError as e:
            self.logger.error(f"Redis error getting remaining requests: {e}")
            return self.limit  # Assume full quota if Redis fails

    def wait_for_slot(self, identifier: str = "default", timeout: Optional[float] = None) -> bool:
        """
        Wait until a request slot becomes available.

        Args:
            identifier: Unique identifier for the rate limit scope
            timeout: Maximum time to wait in seconds (None for no timeout)

        Returns:
            bool: True if slot became available, False if timeout
        """
        start_time = time.time()

        while timeout is None or (time.time() - start_time) < timeout:
            if self.allow_request(identifier):
                return True
            time.sleep(1)  # Wait 1 second before checking again

        return False