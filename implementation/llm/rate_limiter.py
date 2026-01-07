"""
RemDarwin Rate Limiter - Advanced rate limiting for OpenAI API

This module provides sophisticated rate limiting with token bucket algorithms,
exponential backoff, and request queuing for reliable API interactions.
"""

import time
import threading
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import math

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int = 50
    tokens_per_minute: int = 50000  # Conservative estimate
    max_burst_requests: int = 10
    max_burst_tokens: int = 10000
    base_backoff_seconds: float = 1.0
    max_backoff_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    queue_timeout_seconds: float = 300.0  # 5 minutes


@dataclass
class RequestInfo:
    """Information about a queued request"""
    request_id: str
    tokens_estimate: int
    callback: Callable
    args: tuple
    kwargs: dict
    queued_time: datetime
    priority: int = 0  # Higher priority = processed first


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter for requests and tokens

    This implements a dual token bucket system:
    - Request bucket: limits number of API calls
    - Token bucket: limits total tokens consumed
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config

        # Request bucket
        self.request_tokens = config.max_burst_requests
        self.request_rate = config.requests_per_minute / 60.0  # per second
        self.last_request_update = time.time()

        # Token bucket
        self.token_tokens = config.max_burst_tokens
        self.token_rate = config.tokens_per_minute / 60.0  # per second
        self.last_token_update = time.time()

        # Backoff state
        self.current_backoff = config.base_backoff_seconds
        self.consecutive_failures = 0
        self.last_failure_time = None

        # Statistics
        self.total_requests = 0
        self.total_tokens = 0
        self.throttled_requests = 0
        self.queue_timeouts = 0

        logger.info(f"Rate limiter initialized: {config.requests_per_minute} RPM, {config.tokens_per_minute} TPM")

    def _refill_request_tokens(self) -> None:
        """Refill request tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_request_update
        refill_amount = elapsed * self.request_rate
        self.request_tokens = min(
            self.config.max_burst_requests,
            self.request_tokens + refill_amount
        )
        self.last_request_update = now

    def _refill_token_tokens(self) -> None:
        """Refill token tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_token_update
        refill_amount = elapsed * self.token_rate
        self.token_tokens = min(
            self.config.max_burst_tokens,
            self.token_tokens + refill_amount
        )
        self.last_token_update = now

    def _calculate_backoff(self) -> float:
        """Calculate exponential backoff duration"""
        if self.consecutive_failures == 0:
            return 0.0

        backoff = min(
            self.config.base_backoff_seconds * (self.config.backoff_multiplier ** (self.consecutive_failures - 1)),
            self.config.max_backoff_seconds
        )

        # Add jitter to prevent thundering herd
        jitter = backoff * 0.1 * (time.time() % 1)
        return backoff + jitter

    def can_proceed(self, tokens_estimate: int = 1000) -> tuple[bool, float]:
        """
        Check if a request can proceed immediately

        Args:
            tokens_estimate: Estimated tokens for the request

        Returns:
            Tuple of (can_proceed, wait_time_seconds)
        """
        # Check backoff
        if self.current_backoff > 0:
            now = time.time()
            if self.last_failure_time:
                elapsed = now - self.last_failure_time
                if elapsed < self.current_backoff:
                    remaining = self.current_backoff - elapsed
                    return False, remaining

            # Reset backoff if enough time has passed
            self.current_backoff = 0
            self.consecutive_failures = 0

        # Refill tokens
        self._refill_request_tokens()
        self._refill_token_tokens()

        # Check if we have capacity
        has_request_capacity = self.request_tokens >= 1
        has_token_capacity = self.token_tokens >= tokens_estimate

        if has_request_capacity and has_token_capacity:
            return True, 0.0

        # Calculate wait time
        request_wait = 0.0 if has_request_capacity else (1 - self.request_tokens) / self.request_rate
        token_wait = 0.0 if has_token_capacity else (tokens_estimate - self.token_tokens) / self.token_rate

        wait_time = max(request_wait, token_wait)
        return False, wait_time

    def consume_tokens(self, tokens_used: int) -> None:
        """
        Consume tokens after a successful request

        Args:
            tokens_used: Actual tokens consumed
        """
        self.request_tokens -= 1
        self.token_tokens -= tokens_used
        self.total_requests += 1
        self.total_tokens += tokens_used

        # Reset failure state on success
        self.consecutive_failures = 0
        self.current_backoff = 0

    def record_failure(self) -> None:
        """Record a request failure for backoff calculation"""
        self.consecutive_failures += 1
        self.last_failure_time = time.time()
        self.current_backoff = self._calculate_backoff()
        self.throttled_requests += 1

        logger.warning(f"Rate limit failure recorded. Backoff: {self.current_backoff:.2f}s, Failures: {self.consecutive_failures}")

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "throttled_requests": self.throttled_requests,
            "queue_timeouts": self.queue_timeouts,
            "current_request_tokens": self.request_tokens,
            "current_token_tokens": self.token_tokens,
            "consecutive_failures": self.consecutive_failures,
            "current_backoff": self.current_backoff
        }


class RequestQueue:
    """
    Priority queue for rate-limited requests

    Uses a priority queue to handle requests that exceed rate limits,
    with automatic timeout and cleanup.
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.queue: List[RequestInfo] = []
        self.lock = threading.Lock()
        self.next_request_id = 0

    def add_request(self,
                   tokens_estimate: int,
                   callback: Callable,
                   args: tuple = (),
                   kwargs: dict = None,
                   priority: int = 0) -> str:
        """
        Add a request to the queue

        Args:
            tokens_estimate: Estimated tokens for the request
            callback: Function to call when request is processed
            args: Positional arguments for callback
            kwargs: Keyword arguments for callback
            priority: Priority level (higher = processed first)

        Returns:
            Request ID for tracking
        """
        if kwargs is None:
            kwargs = {}

        request_id = f"req_{self.next_request_id}"
        self.next_request_id += 1

        request_info = RequestInfo(
            request_id=request_id,
            tokens_estimate=tokens_estimate,
            callback=callback,
            args=args,
            kwargs=kwargs,
            queued_time=datetime.now(),
            priority=priority
        )

        with self.lock:
            self.queue.append(request_info)
            # Sort by priority (descending) then by time (ascending)
            self.queue.sort(key=lambda x: (-x.priority, x.queued_time))

        logger.debug(f"Request {request_id} queued with priority {priority}")
        return request_id

    def get_next_request(self) -> Optional[RequestInfo]:
        """Get the next request to process"""
        with self.lock:
            if not self.queue:
                return None

            # Check for timeouts
            now = datetime.now()
            while self.queue:
                request = self.queue[0]
                age = (now - request.queued_time).total_seconds()
                if age > self.config.queue_timeout_seconds:
                    self.queue.pop(0)
                    logger.warning(f"Request {request.request_id} timed out after {age:.1f}s")
                    continue
                else:
                    return request

            return None

    def remove_request(self, request_id: str) -> bool:
        """Remove a request from the queue"""
        with self.lock:
            for i, request in enumerate(self.queue):
                if request.request_id == request_id:
                    self.queue.pop(i)
                    logger.debug(f"Request {request_id} removed from queue")
                    return True
            return False

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        with self.lock:
            if not self.queue:
                return {"queue_length": 0, "oldest_request_age": 0}

            now = datetime.now()
            oldest = min(r.queued_time for r in self.queue)
            oldest_age = (now - oldest).total_seconds()

            return {
                "queue_length": len(self.queue),
                "oldest_request_age": oldest_age,
                "priority_distribution": {
                    p: len([r for r in self.queue if r.priority == p])
                    for p in set(r.priority for r in self.queue)
                }
            }


class RateLimitedClient:
    """
    Wrapper that adds rate limiting to any client

    This class wraps API clients and automatically handles rate limiting,
    queuing, and retry logic.
    """

    def __init__(self, client: Any, config: Optional[RateLimitConfig] = None):
        self.client = client
        self.config = config or RateLimitConfig()
        self.rate_limiter = TokenBucketRateLimiter(self.config)
        self.request_queue = RequestQueue(self.config)

        # Background processing thread
        self.processing_thread = None
        self.stop_processing = False

    def start_background_processing(self) -> None:
        """Start background thread to process queued requests"""
        if self.processing_thread and self.processing_thread.is_alive():
            return

        self.stop_processing = False
        self.processing_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.processing_thread.start()
        logger.info("Background request processing started")

    def stop_background_processing(self) -> None:
        """Stop background request processing"""
        self.stop_processing = True
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)
        logger.info("Background request processing stopped")

    def _process_queue(self) -> None:
        """Background thread to process queued requests"""
        while not self.stop_processing:
            try:
                request = self.request_queue.get_next_request()
                if request:
                    # Check if we can process it now
                    can_proceed, wait_time = self.rate_limiter.can_proceed(request.tokens_estimate)

                    if can_proceed:
                        try:
                            # Execute the request
                            result = request.callback(*request.args, **request.kwargs)
                            # Note: In real implementation, you'd need to get actual tokens used
                            # and call consume_tokens appropriately
                            logger.debug(f"Processed queued request {request.request_id}")
                        except Exception as e:
                            logger.error(f"Error processing queued request {request.request_id}: {e}")
                    else:
                        # Still waiting, put back in queue
                        time.sleep(min(wait_time, 1.0))  # Don't sleep too long
                else:
                    # No requests, sleep briefly
                    time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in queue processing: {e}")
                time.sleep(1.0)

    def make_request(self,
                    tokens_estimate: int = 1000,
                    priority: int = 0,
                    queue_if_needed: bool = True) -> Callable:
        """
        Decorator to add rate limiting to API calls

        Args:
            tokens_estimate: Estimated tokens for the request
            priority: Priority level for queuing
            queue_if_needed: Whether to queue if rate limited

        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                # Check if we can proceed
                can_proceed, wait_time = self.rate_limiter.can_proceed(tokens_estimate)

                if can_proceed:
                    try:
                        # Execute immediately
                        start_time = time.time()
                        result = func(*args, **kwargs)
                        execution_time = time.time() - start_time

                        # Extract actual token usage (this would need to be customized per client)
                        # For now, assume estimate is close enough
                        self.rate_limiter.consume_tokens(tokens_estimate)

                        logger.debug(f"Request completed in {execution_time:.2f}s")
                        return result

                    except Exception as e:
                        # Record failure for backoff
                        self.rate_limiter.record_failure()
                        raise

                elif queue_if_needed:
                    # Queue the request
                    def queued_callback(*q_args, **q_kwargs):
                        return func(*q_args, **q_kwargs)

                    request_id = self.request_queue.add_request(
                        tokens_estimate=tokens_estimate,
                        callback=queued_callback,
                        args=args,
                        kwargs=kwargs,
                        priority=priority
                    )

                    logger.info(f"Request queued: {request_id}, wait time: {wait_time:.2f}s")
                    return {"status": "queued", "request_id": request_id, "estimated_wait": wait_time}

                else:
                    # Cannot proceed and not queuing
                    raise Exception(f"Rate limited. Wait {wait_time:.2f} seconds or reduce request frequency.")

            return wrapper
        return decorator

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        return {
            "rate_limiter": self.rate_limiter.get_stats(),
            "queue": self.request_queue.get_queue_stats()
        }


# Default configurations for different use cases
DEFAULT_CONFIGS = {
    "conservative": RateLimitConfig(
        requests_per_minute=30,
        tokens_per_minute=30000,
        max_burst_requests=5,
        max_burst_tokens=5000
    ),
    "balanced": RateLimitConfig(
        requests_per_minute=50,
        tokens_per_minute=50000,
        max_burst_requests=10,
        max_burst_tokens=10000
    ),
    "aggressive": RateLimitConfig(
        requests_per_minute=100,
        tokens_per_minute=100000,
        max_burst_requests=20,
        max_burst_tokens=20000
    )
}


def create_rate_limiter(config_name: str = "balanced") -> RateLimitedClient:
    """
    Factory function to create a rate limiter

    Args:
        config_name: Name of the default configuration to use

    Returns:
        Configured RateLimitedClient (without wrapped client - add separately)
    """
    config = DEFAULT_CONFIGS.get(config_name, DEFAULT_CONFIGS["balanced"])
    # Return a dummy client - in real usage, you'd pass the actual API client
    dummy_client = object()  # Placeholder
    return RateLimitedClient(dummy_client, config)


if __name__ == "__main__":
    # Test the rate limiter
    limiter = create_rate_limiter("balanced")

    print("Rate limiter test:")
    print(f"Initial stats: {limiter.get_stats()}")

    # Test immediate availability
    can_proceed, wait = limiter.rate_limiter.can_proceed(1000)
    print(f"Can proceed immediately: {can_proceed}, wait: {wait:.2f}s")

    # Simulate consumption
    limiter.rate_limiter.consume_tokens(1000)
    print(f"After consumption: {limiter.get_stats()['rate_limiter']}")