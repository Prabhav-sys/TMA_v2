"""Tiny Redis cache helper. If Redis is down the app keeps working, just without caching."""
import json

import redis

from config import Config

_client = None


def client():
    global _client
    if _client is None:
        _client = redis.Redis.from_url(
            Config.REDIS_CACHE_URL, decode_responses=True,
            socket_connect_timeout=0.5, socket_timeout=0.5,
        )
    return _client


def redis_available():
    try:
        return bool(client().ping())
    except Exception:
        return False


def cache_get(key):
    try:
        raw = client().get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


def cache_set(key, value, ttl=None):
    try:
        client().setex(key, ttl or Config.CACHE_TTL, json.dumps(value))
    except Exception:
        pass


def cache_clear_treks():
    """Called after any change to a trek or booking so stale data is never served."""
    try:
        for key in client().scan_iter(match="trek*"):
            client().delete(key)
    except Exception:
        pass
