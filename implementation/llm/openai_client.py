"""
RemDarwin Perplexity Client - Enterprise-grade LLM API integration

This module provides a robust, production-ready wrapper for Perplexity.ai API interactions
with authentication, session management, cost tracking, and error handling.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .rate_limiter import RateLimitedClient, RateLimitConfig
from .monitoring import get_monitoring_system

logger = logging.getLogger(__name__)


# Custom exception classes for comprehensive error handling
class APIError(Exception):
    """Base class for API-related errors"""
    def __init__(self, message: str, response=None, body=None):
        super().__init__(message)
        self.response = response
        self.body = body


class AuthenticationError(APIError):
    """Authentication-related errors"""
    pass


class RateLimitError(APIError):
    """Rate limiting errors"""
    pass


class APIConnectionError(APIError):
    """Network/connection errors"""
    pass


class APITimeoutError(APIError):
    """Timeout errors"""
    pass


class CircuitBreakerOpenError(APIError):
    """Circuit breaker is open"""
    pass


@dataclass
class APIUsage:
    """Track API usage and costs"""
    requests: int = 0
    tokens_prompt: int = 0
    tokens_completion: int = 0
    tokens_total: int = 0
    cost_usd: float = 0.0
    last_request_time: Optional[datetime] = None
    model_usage: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class ClientConfig:
    """Configuration for OpenAI client"""
    api_key: str
    organization: Optional[str] = None
    project: Optional[str] = None
    timeout: float = 60.0
    max_retries: int = 3
    base_url: Optional[str] = None
    default_model: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: int = 4000
    enable_cost_tracking: bool = True
    enable_rate_limiting: bool = True
    rate_limit_config: Optional[RateLimitConfig] = None


class RemDarwinPerplexityClient:
    """
    Production-ready Perplexity.ai API client with enterprise features

    Features:
    - Authentication and session management
    - Automatic cost tracking
    - Circuit breaker pattern for resilience
    - Comprehensive error handling
    - Request/response logging
    - Rate limiting awareness
    """

    # Perplexity API endpoint
    API_BASE_URL = "https://api.perplexity.ai"

    # Cost per request (Perplexity pricing - update as needed)
    # Note: Perplexity pricing is different - they charge per request, not per token
    COST_PER_REQUEST = {
        "llama-3.1-sonar-small-128k-online": 0.005,    # ~$0.005 per request
        "llama-3.1-sonar-large-128k-online": 0.015,    # ~$0.015 per request
        "llama-3.1-sonar-small-128k-chat": 0.005,
        "llama-3.1-sonar-large-128k-chat": 0.015,
    }

    def __init__(self, config: ClientConfig):
        """
        Initialize the Perplexity client

        Args:
            config: Client configuration
        """
        self.config = config
        self.usage = APIUsage()

        # Enhanced circuit breaker state
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = None
        self.circuit_breaker_timeout = 60  # seconds
        self.circuit_breaker_failure_threshold = 5
        self.circuit_breaker_success_threshold = 3  # successes needed to reset
        self.consecutive_successes = 0

        # Comprehensive error tracking
        self.error_counts = {
            "rate_limit": 0,
            "authentication": 0,
            "connection": 0,
            "timeout": 0,
            "malformed_response": 0,
            "server_error": 0,
            "other": 0
        }
        self.last_errors = []  # Keep last 10 errors for analysis
        self.error_tracking_window = 300  # 5 minutes

        # Initialize HTTP session with retry strategy
        self.session = self._create_session()

        # Initialize rate limiter if enabled
        self.rate_limiter = None
        if config.enable_rate_limiting:
            from .rate_limiter import RateLimitedClient
            rate_limited_client = RateLimitedClient(self, config.rate_limit_config)
            self.rate_limiter = rate_limited_client
            rate_limited_client.start_background_processing()
            logger.info("Rate limiter initialized and background processing started")

        # Initialize monitoring
        self.monitoring = get_monitoring_system()
        self.monitoring_enabled = True

        logger.info("Perplexity client initialized successfully")

    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry configuration"""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        # Set default headers
        session.headers.update({
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        })

        return session

    def __del__(self):
        """Cleanup session on destruction"""
        if hasattr(self, 'session'):
            self.session.close()

    @classmethod
    def from_env(cls, **overrides) -> "RemDarwinPerplexityClient":
        """
        Create client from environment variables

        Args:
            **overrides: Override default configuration

        Returns:
            Configured client instance
        """
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable is required")

        config = ClientConfig(
            api_key=api_key,
            default_model="llama-3.1-sonar-small-128k-online",  # Perplexity default model
            **overrides
        )

        return cls(config)

    def _check_circuit_breaker(self) -> None:
        """
        Enhanced circuit breaker with hysteresis and error pattern analysis

        Raises APIConnectionError if circuit is open
        """
        # Check if circuit breaker should be open
        if self.circuit_breaker_failures >= self.circuit_breaker_failure_threshold:
            if self.circuit_breaker_last_failure:
                time_since_failure = (datetime.now() - self.circuit_breaker_last_failure).total_seconds()

                # Still in timeout period
                if time_since_failure < self.circuit_breaker_timeout:
                    remaining_time = self.circuit_breaker_timeout - time_since_failure
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker open for {remaining_time:.1f}s - {self.circuit_breaker_failures} failures"
                    )

                # Timeout expired, check for recent success pattern
                elif self.consecutive_successes < self.circuit_breaker_success_threshold:
                    logger.warning(f"Circuit breaker timeout expired but insufficient successes "
                                 f"({self.consecutive_successes}/{self.circuit_breaker_success_threshold})")
                    raise CircuitBreakerOpenError("Circuit breaker: insufficient recent successes")

            # Reset circuit breaker after timeout
            logger.info("Circuit breaker reset after timeout period")
            self._reset_circuit_breaker()

    def _reset_circuit_breaker(self) -> None:
        """Reset circuit breaker state"""
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = None
        self.consecutive_successes = 0

    def _record_circuit_breaker_success(self) -> None:
        """Record a successful request for circuit breaker recovery"""
        self.consecutive_successes += 1
        if self.consecutive_successes >= self.circuit_breaker_success_threshold:
            # Full recovery achieved
            self.circuit_breaker_failures = max(0, self.circuit_breaker_failures - 1)

    def _record_circuit_breaker_failure(self, error: Exception) -> None:
        """Record a failure and update circuit breaker state"""
        self.circuit_breaker_failures += 1
        self.circuit_breaker_last_failure = datetime.now()
        self.consecutive_successes = 0

        # Categorize the error
        self._categorize_error(error)

    def _handle_error(self, error: Exception, context: str) -> None:
        """
        Comprehensive error handling with circuit breaker, logging, and recovery strategies

        Args:
            error: The exception that occurred
            context: Context information about where the error occurred
        """
        # Record failure in circuit breaker
        self._record_circuit_breaker_failure(error)

        # Track error for analysis
        self._track_error(error, context)

        # Categorize and handle different error types
        if isinstance(error, requests.exceptions.RequestException):
            self._handle_request_error(error, context)
        elif isinstance(error, RateLimitError):
            self._handle_rate_limit_error(error, context)
        elif isinstance(error, AuthenticationError):
            self._handle_authentication_error(error, context)
        elif isinstance(error, APIError):
            self._handle_api_error(error, context)
        else:
            self._handle_unexpected_error(error, context)

    def _handle_request_error(self, error: requests.exceptions.RequestException, context: str) -> None:
        """Handle HTTP request-related errors"""
        if isinstance(error, requests.exceptions.Timeout):
            logger.warning(f"Request timeout in {context}: {error}")
            raise APITimeoutError(f"Request timed out: {error}", response=None, body=None)
        elif isinstance(error, requests.exceptions.ConnectionError):
            logger.warning(f"Connection error in {context}: {error}")
            raise APIConnectionError(f"Connection failed: {error}", response=None, body=None)
        elif isinstance(error, requests.exceptions.HTTPError):
            status_code = error.response.status_code if error.response else None
            if status_code == 429:
                logger.warning(f"Rate limit HTTP error in {context}: {status_code}")
                raise RateLimitError(f"HTTP 429 Rate Limit: {error}", response=error.response, body=None)
            elif status_code == 401:
                logger.error(f"Authentication HTTP error in {context}: {status_code}")
                raise AuthenticationError(f"HTTP 401 Authentication Failed: {error}", response=error.response, body=None)
            elif status_code >= 500:
                logger.warning(f"Server error in {context}: HTTP {status_code}")
                raise APIConnectionError(f"HTTP {status_code} Server Error: {error}", response=error.response, body=None)
            else:
                logger.error(f"HTTP error in {context}: {status_code} - {error}")
                raise APIError(f"HTTP {status_code}: {error}", response=error.response, body=None)
        else:
            logger.warning(f"Request exception in {context}: {error}")
            raise APIConnectionError(f"Request failed: {error}", response=None, body=None)

    def _handle_rate_limit_error(self, error: RateLimitError, context: str) -> None:
        """Handle rate limiting errors with backoff strategy"""
        logger.warning(f"Rate limit exceeded in {context}: {error}")
        # Rate limit errors are automatically handled by rate limiter
        # Re-raise to let calling code handle queuing/retry
        raise

    def _handle_authentication_error(self, error: AuthenticationError, context: str) -> None:
        """Handle authentication failures"""
        logger.error(f"Authentication failed in {context}: {error}")
        logger.error("Please check PERPLEXITY_API_KEY environment variable")
        # Authentication errors are critical - re-raise immediately
        raise

    def _handle_api_error(self, error: APIError, context: str) -> None:
        """Handle general API errors"""
        logger.error(f"API error in {context}: {error}")

        # Check if this is a malformed response error
        if "malformed" in str(error).lower() or "invalid json" in str(error).lower():
            logger.warning("Detected malformed response - may indicate API format changes")
            self._log_malformed_response_warning()

        raise

    def _handle_unexpected_error(self, error: Exception, context: str) -> None:
        """Handle unexpected errors"""
        logger.error(f"Unexpected error in {context}: {type(error).__name__}: {error}")
        logger.error(f"Error details: {repr(error)}")

        # Log additional context for debugging
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")

        raise APIError(f"Unexpected error: {error}", response=None, body=None)

    def _log_malformed_response_warning(self) -> None:
        """Log warnings about potential API changes"""
        logger.warning("=" * 60)
        logger.warning("MALFORMED RESPONSE DETECTED")
        logger.warning("This may indicate API format changes or network issues")
        logger.warning("Consider updating response parsing logic")
        logger.warning("=" * 60)

    def _categorize_error(self, error: Exception) -> None:
        """Categorize error for tracking and analysis"""
        if isinstance(error, RateLimitError):
            self.error_counts["rate_limit"] += 1
        elif isinstance(error, AuthenticationError):
            self.error_counts["authentication"] += 1
        elif isinstance(error, APIConnectionError):
            if "timeout" in str(error).lower():
                self.error_counts["timeout"] += 1
            else:
                self.error_counts["connection"] += 1
        elif isinstance(error, APIError):
            if "malformed" in str(error).lower() or "invalid json" in str(error).lower():
                self.error_counts["malformed_response"] += 1
            elif hasattr(error, 'response') and error.response:
                if error.response.status_code >= 500:
                    self.error_counts["server_error"] += 1
                else:
                    self.error_counts["other"] += 1
            else:
                self.error_counts["other"] += 1
        else:
            self.error_counts["other"] += 1

    def _track_error(self, error: Exception, context: str) -> None:
        """Track error for analysis and monitoring"""
        error_info = {
            "timestamp": datetime.now(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }

        self.last_errors.append(error_info)

        # Keep only recent errors (last 10, or within time window)
        cutoff_time = datetime.now() - timedelta(seconds=self.error_tracking_window)
        self.last_errors = [
            e for e in self.last_errors
            if e["timestamp"] > cutoff_time
        ][-10:]  # Keep max 10

    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive error statistics for monitoring

        Returns:
            Dictionary with error statistics and recent errors
        """
        return {
            "error_counts": self.error_counts.copy(),
            "total_errors": sum(self.error_counts.values()),
            "circuit_breaker_state": {
                "failures": self.circuit_breaker_failures,
                "last_failure": self.circuit_breaker_last_failure.isoformat() if self.circuit_breaker_last_failure else None,
                "consecutive_successes": self.consecutive_successes,
                "is_open": self.circuit_breaker_failures >= self.circuit_breaker_failure_threshold
            },
            "recent_errors": [
                {
                    "timestamp": e["timestamp"].isoformat(),
                    "error_type": e["error_type"],
                    "context": e["context"]
                }
                for e in self.last_errors[-5:]  # Last 5 errors
            ]
        }

    def _update_usage(self, model: str, usage: Dict[str, Any]) -> None:
        """Update usage tracking"""
        if not self.config.enable_cost_tracking:
            return

        self.usage.requests += 1
        self.usage.last_request_time = datetime.now()

        # Extract token usage
        tokens_prompt = usage.get("prompt_tokens", 0)
        tokens_completion = usage.get("completion_tokens", 0)
        tokens_total = usage.get("total_tokens", tokens_prompt + tokens_completion)

        self.usage.tokens_prompt += tokens_prompt
        self.usage.tokens_completion += tokens_completion
        self.usage.tokens_total += tokens_total

        # Calculate cost
        if model in self.COST_PER_1K_TOKENS:
            rates = self.COST_PER_1K_TOKENS[model]
            cost = (tokens_prompt / 1000 * rates["prompt"] +
                   tokens_completion / 1000 * rates["completion"])
            self.usage.cost_usd += cost

        # Track per-model usage
        if model not in self.usage.model_usage:
            self.usage.model_usage[model] = {"requests": 0, "tokens": 0, "cost": 0.0}

        self.usage.model_usage[model]["requests"] += 1
        self.usage.model_usage[model]["tokens"] += tokens_total
        self.usage.model_usage[model]["cost"] += cost

        logger.debug(f"Usage updated: {model} - {tokens_total} tokens, ${cost:.4f}")

    def _update_usage_perplexity(self, model: str, usage: Dict[str, Any]) -> None:
        """Update usage tracking for Perplexity API (request-based pricing)"""
        if not self.config.enable_cost_tracking:
            return

        self.usage.requests += 1
        self.usage.last_request_time = datetime.now()

        # Extract token usage (may not be provided by Perplexity)
        tokens_prompt = usage.get("prompt_tokens", 0)
        tokens_completion = usage.get("completion_tokens", 0)
        tokens_total = usage.get("total_tokens", tokens_prompt + tokens_completion)

        self.usage.tokens_prompt += tokens_prompt
        self.usage.tokens_completion += tokens_completion
        self.usage.tokens_total += tokens_total

        # Calculate cost (Perplexity charges per request, not per token)
        cost = self.COST_PER_REQUEST.get(model, 0.005)  # Default to $0.005 if model not found
        self.usage.cost_usd += cost

        # Track per-model usage
        if model not in self.usage.model_usage:
            self.usage.model_usage[model] = {"requests": 0, "tokens": 0, "cost": 0.0}

        self.usage.model_usage[model]["requests"] += 1
        self.usage.model_usage[model]["tokens"] += tokens_total
        self.usage.model_usage[model]["cost"] += cost

        logger.debug(f"Perplexity usage updated: {model} - {tokens_total} tokens, ${cost:.4f}")

    def create_completion(self,
                         messages: List[Dict[str, str]],
                         model: Optional[str] = None,
                         **kwargs) -> Dict[str, Any]:
        """
        Create a chat completion with comprehensive error handling and rate limiting

        Args:
            messages: List of message dictionaries
            model: Model to use (defaults to config.default_model)
            **kwargs: Additional parameters for the completion

        Returns:
            Completion response dictionary
        """
        self._check_circuit_breaker()

        model = model or self.config.default_model

        # Estimate tokens for rate limiting
        token_estimate = self._estimate_tokens(messages, model, kwargs)

        # Use rate limiter if enabled
        if self.rate_limiter:
            # Create the API call function
            def api_call():
                return self._execute_completion(model, messages, **kwargs)

            # Apply rate limiting
            rate_limited_call = self.rate_limiter.make_request(
                tokens_estimate=token_estimate,
                priority=1  # High priority for real-time requests
            )(api_call)

            try:
                return rate_limited_call()
            except Exception as e:
                if "queued" in str(e).lower():
                    # Request was queued, handle appropriately
                    logger.warning(f"Request queued due to rate limiting: {e}")
                    raise RateLimitError("Request queued due to rate limiting", response=None, body=None)
                raise

        else:
            # No rate limiting, execute directly
            return self._execute_completion(model, messages, **kwargs)

    def _estimate_tokens(self, messages: List[Dict[str, str]], model: str, kwargs: Dict[str, Any]) -> int:
        """
        Estimate token count for rate limiting purposes

        Args:
            messages: Message list
            model: Model name
            kwargs: Additional parameters

        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        base_tokens = total_chars // 4

        # Add tokens for completion (rough estimate)
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        estimated_total = base_tokens + max_tokens

        return min(estimated_total, 10000)  # Cap at reasonable maximum

    def _execute_completion(self, model: str, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Execute the actual completion call using Perplexity API

        Args:
            model: Model to use
            messages: Message list
            **kwargs: Additional parameters

        Returns:
            Completion response dictionary
        """
        # Prepare payload for Perplexity API
        payload = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }

        # Add any additional kwargs (excluding our handled ones)
        for key, value in kwargs.items():
            if key not in ["temperature", "max_tokens"]:
                payload[key] = value

        start_time = time.time()
        try:
            logger.info(f"Creating completion with Perplexity model {model}")

            # Make HTTP request to Perplexity API
            response = self.session.post(
                f"{self.API_BASE_URL}/chat/completions",
                json=payload,
                timeout=self.config.timeout
            )

            response.raise_for_status()
            response_data = response.json()

            # Extract response data in consistent format
            result = {
                "id": response_data.get("id", "perplexity-" + str(int(time.time()))),
                "model": response_data.get("model", model),
                "content": response_data["choices"][0]["message"]["content"],
                "finish_reason": response_data["choices"][0].get("finish_reason", "completed"),
                "usage": {
                    "prompt_tokens": response_data.get("usage", {}).get("prompt_tokens", 0),
                    "completion_tokens": response_data.get("usage", {}).get("completion_tokens", 0),
                    "total_tokens": response_data.get("usage", {}).get("total_tokens", 0)
                },
                "processing_time": time.time() - start_time
            }

            # Update usage tracking (Perplexity charges per request, not per token)
            self._update_usage_perplexity(model, result["usage"])

            # Update rate limiter with actual token usage
            if self.rate_limiter:
                self.rate_limiter.rate_limiter.consume_tokens(result["usage"]["total_tokens"])

            # Record success for circuit breaker recovery
            self._record_circuit_breaker_success()

            # Record metrics for monitoring
            tokens_used = result["usage"]["total_tokens"]
            cost_usd = self.COST_PER_REQUEST.get(model, 0.005)  # Perplexity charges per request
            if self.monitoring_enabled:
                self.monitoring.record_api_call(
                    model=model,
                    latency_ms=result["processing_time"] * 1000,
                    tokens=tokens_used,
                    cost_usd=cost_usd,
                    success=True
                )

            logger.info(f"Completion successful: {result['id']} ({result['processing_time']:.2f}s)")
            return result

        except requests.exceptions.RequestException as e:
            processing_time = time.time() - start_time
            logger.warning(f"Completion failed after {processing_time:.2f}s: {e}")

            # Record failure metrics for monitoring
            if self.monitoring_enabled:
                error_type = type(e).__name__
                self.monitoring.record_api_call(
                    model=model,
                    latency_ms=processing_time * 1000,
                    tokens=0,  # No tokens consumed on failure
                    cost_usd=0.0,  # No cost on failure
                    success=False,
                    error_type=error_type
                )

            self._handle_error(e, f"create_completion (model: {model})")

            # Record failure in rate limiter
            if self.rate_limiter:
                self.rate_limiter.rate_limiter.record_failure()

            raise

    def validate_connection(self) -> bool:
        """
        Test the connection to Perplexity API

        Returns:
            True if connection is successful
        """
        try:
            # Simple test completion
            response = self.session.post(
                f"{self.API_BASE_URL}/chat/completions",
                json={
                    "model": self.config.default_model,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 5
                },
                timeout=10  # Shorter timeout for validation
            )
            response.raise_for_status()
            logger.info("Perplexity connection validated successfully")
            return True
        except Exception as e:
            logger.error(f"Perplexity connection validation failed: {e}")
            return False

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive usage and error statistics

        Returns:
            Dictionary with usage statistics and error tracking
        """
        error_stats = self.get_error_statistics()

        return {
            "total_requests": self.usage.requests,
            "total_tokens": self.usage.tokens_total,
            "total_cost_usd": round(self.usage.cost_usd, 4),
            "avg_cost_per_request": round(self.usage.cost_usd / max(self.usage.requests, 1), 4),
            "model_breakdown": self.usage.model_usage,
            "last_request_time": self.usage.last_request_time.isoformat() if self.usage.last_request_time else None,
            "error_statistics": error_stats,
            "success_rate": round(
                (self.usage.requests - sum(error_stats["error_counts"].values())) /
                max(self.usage.requests, 1) * 100, 2
            )
        }

    def reset_usage_stats(self) -> None:
        """Reset usage statistics"""
        self.usage = APIUsage()
        logger.info("Usage statistics reset")


def create_client_from_config() -> RemDarwinPerplexityClient:
    """
    Factory function to create client from environment configuration

    Returns:
        Configured Perplexity client
    """
    return RemDarwinPerplexityClient.from_env()


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        # Create client (requires PERPLEXITY_API_KEY in environment)
        client = create_client_from_config()

        # Validate connection
        if client.validate_connection():
            print("✅ Perplexity client connection validated")

            # Test completion
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello in French"}
            ]

            result = client.create_completion(messages)
            print(f"✅ Completion successful: {result['content']}")

            # Show usage stats
            stats = client.get_usage_stats()
            print(f"📊 Usage: {stats['total_requests']} requests, ${stats['total_cost_usd']}")

        else:
            print("❌ Connection validation failed")

    except Exception as e:
        print(f"❌ Client setup failed: {e}")