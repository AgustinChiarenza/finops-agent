import time
from typing import Any

from app.config import settings


class TTLCache:
    def __init__(self, ttl: int | None = None):
        self.ttl = ttl or settings.cache_ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        if key in self._store:
            expires_at, value = self._store[key]
            if time.time() < expires_at:
                return value
            del self._store[key]
        return None

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.time() + self.ttl, value)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def cached(self, key: str):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                cached_val = self.get(key)
                if cached_val is not None:
                    return cached_val
                result = await func(*args, **kwargs)
                self.set(key, result)
                return result
            return wrapper
        return decorator


cache = TTLCache()
