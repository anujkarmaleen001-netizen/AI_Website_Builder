"""
Rate limiting implementation to prevent API abuse.
"""
import time
import threading
from collections import defaultdict
from typing import Optional, Dict
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimitBucket:
    """Token bucket for rate limiting."""
    capacity: int
    tokens: float
    last_update: float = field(default_factory=time.time)
    refill_rate: float = 1.0  # tokens per second


class RateLimiter:
    """Token bucket rate limiter implementation."""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute
            requests_per_hour: Maximum requests per hour
            burst_size: Maximum burst size
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size
        
        # Token buckets per client (IP address)
        self._minute_buckets: Dict[str, RateLimitBucket] = defaultdict(
            lambda: RateLimitBucket(
                capacity=requests_per_minute,
                tokens=requests_per_minute,
                refill_rate=requests_per_minute / 60.0
            )
        )
        
        self._hour_buckets: Dict[str, RateLimitBucket] = defaultdict(
            lambda: RateLimitBucket(
                capacity=requests_per_hour,
                tokens=requests_per_hour,
                refill_rate=requests_per_hour / 3600.0
            )
        )
        
        self._lock = threading.Lock()
        self._last_cleanup = time.time()
    
    def _refill_bucket(self, bucket: RateLimitBucket) -> None:
        """
        Refill tokens in bucket based on elapsed time.
        
        Args:
            bucket: Rate limit bucket
        """
        now = time.time()
        elapsed = now - bucket.last_update
        
        # Add tokens based on refill rate
        tokens_to_add = elapsed * bucket.refill_rate
        bucket.tokens = min(bucket.capacity, bucket.tokens + tokens_to_add)
        bucket.last_update = now
    
    def _cleanup_old_buckets(self) -> None:
        """Remove old buckets to prevent memory leaks."""
        now = time.time()
        
        # Cleanup every 5 minutes
        if now - self._last_cleanup < 300:
            return
        
        # Remove buckets not used in last hour
        cutoff = now - 3600
        
        self._minute_buckets = defaultdict(
            lambda: RateLimitBucket(
                capacity=self.requests_per_minute,
                tokens=self.requests_per_minute,
                refill_rate=self.requests_per_minute / 60.0
            ),
            {
                k: v for k, v in self._minute_buckets.items()
                if v.last_update > cutoff
            }
        )
        
        self._hour_buckets = defaultdict(
            lambda: RateLimitBucket(
                capacity=self.requests_per_hour,
                tokens=self.requests_per_hour,
                refill_rate=self.requests_per_hour / 3600.0
            ),
            {
                k: v for k, v in self._hour_buckets.items()
                if v.last_update > cutoff
            }
        )
        
        self._last_cleanup = now
    
    def check_rate_limit(self, client_id: str) -> tuple[bool, Optional[int]]:
        """
        Check if request is within rate limit.
        
        Args:
            client_id: Client identifier (e.g., IP address)
            
        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        with self._lock:
            # Periodic cleanup
            self._cleanup_old_buckets()
            
            # Get buckets for client
            minute_bucket = self._minute_buckets[client_id]
            hour_bucket = self._hour_buckets[client_id]
            
            # Refill buckets
            self._refill_bucket(minute_bucket)
            self._refill_bucket(hour_bucket)
            
            # Check if we have tokens in both buckets
            if minute_bucket.tokens < 1:
                # Calculate retry after based on minute bucket
                retry_after = int((1 - minute_bucket.tokens) / minute_bucket.refill_rate) + 1
                logger.warning(
                    f"Rate limit exceeded for {client_id} (per minute). "
                    f"Retry after {retry_after}s"
                )
                return False, retry_after
            
            if hour_bucket.tokens < 1:
                # Calculate retry after based on hour bucket
                retry_after = int((1 - hour_bucket.tokens) / hour_bucket.refill_rate) + 1
                logger.warning(
                    f"Rate limit exceeded for {client_id} (per hour). "
                    f"Retry after {retry_after}s"
                )
                return False, retry_after
            
            # Consume tokens
            minute_bucket.tokens -= 1
            hour_bucket.tokens -= 1
            
            return True, None
    
    def get_remaining(self, client_id: str) -> Dict[str, int]:
        """
        Get remaining requests for client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dictionary with remaining requests per window
        """
        with self._lock:
            minute_bucket = self._minute_buckets[client_id]
            hour_bucket = self._hour_buckets[client_id]
            
            self._refill_bucket(minute_bucket)
            self._refill_bucket(hour_bucket)
            
            return {
                'remaining_minute': int(minute_bucket.tokens),
                'remaining_hour': int(hour_bucket.tokens),
                'limit_minute': self.requests_per_minute,
                'limit_hour': self.requests_per_hour
            }
    
    def reset(self, client_id: Optional[str] = None) -> None:
        """
        Reset rate limit for client or all clients.
        
        Args:
            client_id: Client identifier or None to reset all
        """
        with self._lock:
            if client_id:
                if client_id in self._minute_buckets:
                    del self._minute_buckets[client_id]
                if client_id in self._hour_buckets:
                    del self._hour_buckets[client_id]
            else:
                self._minute_buckets.clear()
                self._hour_buckets.clear()
    
    def get_stats(self) -> Dict[str, any]:
        """Get rate limiter statistics."""
        with self._lock:
            return {
                'active_clients': len(self._minute_buckets),
                'requests_per_minute': self.requests_per_minute,
                'requests_per_hour': self.requests_per_hour,
                'burst_size': self.burst_size
            }


class EndpointRateLimiter:
    """Rate limiter with per-endpoint configuration."""
    
    def __init__(self, default_config: Optional[Dict] = None):
        """
        Initialize endpoint rate limiter.
        
        Args:
            default_config: Default rate limit configuration
        """
        default_config = default_config or {}
        self._default_limiter = RateLimiter(
            requests_per_minute=default_config.get('requests_per_minute', 60),
            requests_per_hour=default_config.get('requests_per_hour', 1000),
            burst_size=default_config.get('burst_size', 10)
        )
        self._endpoint_limiters: Dict[str, RateLimiter] = {}
        self._lock = threading.Lock()
    
    def configure_endpoint(
        self,
        endpoint: str,
        requests_per_minute: int,
        requests_per_hour: int,
        burst_size: int = 10
    ) -> None:
        """
        Configure rate limit for specific endpoint.
        
        Args:
            endpoint: Endpoint path
            requests_per_minute: Requests per minute
            requests_per_hour: Requests per hour
            burst_size: Burst size
        """
        with self._lock:
            self._endpoint_limiters[endpoint] = RateLimiter(
                requests_per_minute=requests_per_minute,
                requests_per_hour=requests_per_hour,
                burst_size=burst_size
            )
    
    def check_rate_limit(
        self,
        client_id: str,
        endpoint: Optional[str] = None
    ) -> tuple[bool, Optional[int]]:
        """
        Check rate limit for client and endpoint.
        
        Args:
            client_id: Client identifier
            endpoint: Endpoint path (optional)
            
        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        with self._lock:
            limiter = self._endpoint_limiters.get(endpoint, self._default_limiter)
        
        return limiter.check_rate_limit(client_id)
    
    def get_remaining(
        self,
        client_id: str,
        endpoint: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Get remaining requests for client and endpoint.
        
        Args:
            client_id: Client identifier
            endpoint: Endpoint path (optional)
            
        Returns:
            Dictionary with remaining requests
        """
        with self._lock:
            limiter = self._endpoint_limiters.get(endpoint, self._default_limiter)
        
        return limiter.get_remaining(client_id)


# Global rate limiter instance
_rate_limiter: Optional[EndpointRateLimiter] = None


def get_rate_limiter(config: Optional[Dict] = None) -> EndpointRateLimiter:
    """
    Get global rate limiter instance.
    
    Args:
        config: Configuration (only used on first call)
        
    Returns:
        EndpointRateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = EndpointRateLimiter(config)
    return _rate_limiter


def init_rate_limiter(config: Dict) -> None:
    """
    Initialize global rate limiter.
    
    Args:
        config: Configuration dictionary
    """
    global _rate_limiter
    _rate_limiter = EndpointRateLimiter(config)
