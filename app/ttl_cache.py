"""Tiny process-local TTL cache for hot list endpoints.

Remote MySQL (Railway) is high-latency; caching list payloads for a few seconds
makes refresh / re-navigation feel instant without Redis.
"""

from __future__ import annotations

import time
from typing import Any


class TtlCache:
  def __init__(self, ttl_sec: float = 20.0):
    self.ttl_sec = ttl_sec
    self._store: dict[str, dict[str, Any]] = {}

  def get(self, key: str):
    entry = self._store.get(key)
    if entry is None:
      return None
    if time.monotonic() >= entry["expires"]:
      self._store.pop(key, None)
      return None
    return entry["payload"]

  def set(self, key: str, payload):
    self._store[key] = {
      "payload": payload,
      "expires": time.monotonic() + self.ttl_sec,
    }

  def invalidate(self, prefix: str | None = None):
    if prefix is None:
      self._store.clear()
      return
    for key in list(self._store):
      if key.startswith(prefix):
        self._store.pop(key, None)


# Shared caches (short TTL — stale for at most ~20s after writes)
projects_cache = TtlCache(20)
users_cache = TtlCache(20)
