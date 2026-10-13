import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import Response


class InMemoryRateLimiter:
    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests: defaultdict[str, deque[float]] = defaultdict(deque)

    def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        timestamps = self.requests[key]
        while timestamps and now - timestamps[0] >= self.window_seconds:
            timestamps.popleft()
        if len(timestamps) >= self.limit:
            return False
        timestamps.append(now)
        return True


def rate_limit_middleware(limiter: InMemoryRateLimiter):
    async def middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path == "/health":
            return await call_next(request)
        client = request.client.host if request.client else "unknown"
        if not limiter.is_allowed(client):
            return Response(
                content='{"detail":"Too many requests. Please try again shortly."}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(limiter.window_seconds)},
            )
        return await call_next(request)

    return middleware
