"""Composable decorators for MemoryStore implementations."""

from __future__ import annotations

from threading import RLock

from .storage import MemoryStore, validate_id, validate_value


class DecoratingMemoryStore(MemoryStore):
    """Delegating base decorator. The outer decorator owns the delegate lifecycle."""

    def __init__(self, delegate: MemoryStore) -> None:
        if delegate is None:
            raise ValueError("delegate must not be None")
        self._delegate = delegate

    def put(self, memory_id: str, value: str) -> None:
        self._delegate.put(memory_id, value)

    def get(self, memory_id: str) -> str | None:
        return self._delegate.get(memory_id)

    def delete(self, memory_id: str) -> bool:
        return self._delegate.delete(memory_id)

    def list_ids(self) -> list[str]:
        return self._delegate.list_ids()

    def close(self) -> None:
        self._delegate.close()


class RamCacheMemoryStore(DecoratingMemoryStore):
    """Read-through/write-through RAM cache around any MemoryStore.

    The delegate remains authoritative. Cache coherence covers operations made
    through this decorator only; out-of-band delegate changes are not observed.
    """

    def __init__(self, delegate: MemoryStore) -> None:
        super().__init__(delegate)
        self._cache: dict[str, str] = {}
        self._lock = RLock()

    def put(self, memory_id: str, value: str) -> None:
        checked_id = validate_id(memory_id)
        checked_value = validate_value(value)
        with self._lock:
            self._delegate.put(checked_id, checked_value)
            self._cache[checked_id] = checked_value

    def get(self, memory_id: str) -> str | None:
        checked_id = validate_id(memory_id)
        with self._lock:
            if checked_id in self._cache:
                return self._cache[checked_id]
            value = self._delegate.get(checked_id)
            if value is not None:
                self._cache[checked_id] = value
            return value

    def delete(self, memory_id: str) -> bool:
        checked_id = validate_id(memory_id)
        with self._lock:
            deleted = self._delegate.delete(checked_id)
            self._cache.pop(checked_id, None)
            return deleted

    def list_ids(self) -> list[str]:
        with self._lock:
            return self._delegate.list_ids()

    def close(self) -> None:
        with self._lock:
            self._cache.clear()
            super().close()
