import time
import redis
from config import REDIS_URL

class TokenBucket:
    """
    Token bucket rate limiter with Redis backend (mock fallback supported).
    - If Redis is available: use distributed token bucket
    - If Redis is not available: fallback to in-memory local bucket (mock mode)
    """

    _local_state = {}  # shared state for in-memory mode

    def __init__(self, user_key: str, capacity=5, refill_rate=0.5):
        self.user_key = user_key
        self.capacity = capacity
        self.refill_rate = refill_rate

        # Try to connect to Redis once
        try:
            self.r = redis.from_url(REDIS_URL)
            self.r.ping()
            self.use_redis = True
        except Exception:
            print("⚠️ Redis not available → using in-memory mock rate limiter")
            self.use_redis = False

    def allow(self) -> bool:
        """
        Try to consume one token. Return True if allowed, False otherwise.
        """
        now = time.time()

        # ------------------------
        # Mock (in-memory) fallback
        # ------------------------
        if not self.use_redis:
            bucket = self._local_state.get(self.user_key, {"tokens": self.capacity, "ts": now})
            tokens = bucket["tokens"]
            last_ts = bucket["ts"]

            # refill
            tokens = min(self.capacity, tokens + (now - last_ts) * self.refill_rate)
            allowed = tokens >= 1
            if allowed:
                tokens -= 1

            # store back
            self._local_state[self.user_key] = {"tokens": tokens, "ts": now}
            return allowed

        # ------------------------
        # Normal Redis-based limiter
        # ------------------------
        pipe = self.r.pipeline()
        pipe.get(f"tb:{self.user_key}:tokens")
        pipe.get(f"tb:{self.user_key}:ts")
        tokens, last_ts = pipe.execute()

        tokens = float(tokens) if tokens else self.capacity
        last_ts = float(last_ts) if last_ts else now

        tokens = min(self.capacity, tokens + (now - last_ts) * self.refill_rate)
        allowed = tokens >= 1.0
        if allowed:
            tokens -= 1.0

        pipe = self.r.pipeline()
        pipe.set(f"tb:{self.user_key}:tokens", tokens)
        pipe.set(f"tb:{self.user_key}:ts", now)
        pipe.execute()

        return allowed
