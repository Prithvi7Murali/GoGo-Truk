import json
from app.config import settings

_redis = None


def _get_client():
    global _redis
    if _redis is not None:
        return _redis
    if not settings.REDIS_URL:
        return None
    try:
        import redis
        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        _redis.ping()
        return _redis
    except Exception:
        return None


def cache_get(key: str):
    client = _get_client()
    if client is None:
        return None
    try:
        value = client.get(key)
        return json.loads(value) if value else None
    except Exception:
        return None


def cache_set(key: str, value, ttl_seconds: int = 300):
    client = _get_client()
    if client is None:
        return
    try:
        client.setex(key, ttl_seconds, json.dumps(value, default=str))
    except Exception:
        pass


def cache_delete_pattern(pattern: str):
    client = _get_client()
    if client is None:
        return
    try:
        keys = client.keys(pattern)
        if keys:
            client.delete(*keys)
    except Exception:
        pass


def acquire_lock(key: str, ttl: int = 30) -> bool:
    """Returns True if lock acquired. Falls back to True (DB lock only) when Redis unavailable."""
    client = _get_client()
    if client is None:
        return True
    try:
        return client.set(key, "1", nx=True, ex=ttl) is not None
    except Exception:
        return True


def release_lock(key: str):
    client = _get_client()
    if client is None:
        return
    try:
        client.delete(key)
    except Exception:
        pass
