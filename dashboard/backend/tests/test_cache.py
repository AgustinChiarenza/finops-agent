import asyncio
import time

from app.cache import TTLCache


def test_cache_set_and_get():
    cache = TTLCache(ttl=60)
    cache.set("k", {"v": 1})
    assert cache.get("k") == {"v": 1}


def test_cache_miss_returns_none():
    cache = TTLCache(ttl=60)
    assert cache.get("missing") is None


def test_cache_expires():
    cache = TTLCache(ttl=1)
    cache.set("k", "v")
    # Wait past TTL
    time.sleep(1.1)
    assert cache.get("k") is None


def test_cache_delete_and_clear():
    cache = TTLCache(ttl=60)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.delete("a")
    assert cache.get("a") is None
    assert cache.get("b") == 2
    cache.clear()
    assert cache.get("b") is None


def test_cached_decorator_caches_result():
    cache = TTLCache(ttl=60)
    calls = {"n": 0}

    @cache.cached("expensive")
    async def expensive():
        calls["n"] += 1
        return calls["n"]

    assert asyncio.run(expensive()) == 1
    assert asyncio.run(expensive()) == 1  # served from cache, not recomputed
