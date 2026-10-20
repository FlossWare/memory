"""Simple process-local RAM backend."""

from __future__ import annotations

from threading import RLock

from .storage import MemoryStore, validate_id, validate_value


class RamMemoryStore(MemoryStore):
    """Thread-safe in-process dictionary; contents are intentionally ephemeral."""

    def __init__(self) -> None:
        self._values: dict[str, str] = {}
        self._lock = RLock()

    def put(self, memory_id: str, value: str) -> None:
        with self._lock:
            self._values[validate_id(memory_id)] = validate_value(value)

    def get(self, memory_id: str) -> str | None:
        with self._lock:
            return self._values.get(validate_id(memory_id))

    def delete(self, memory_id: str) -> bool:
        with self._lock:
            return self._values.pop(validate_id(memory_id), None) is not None

    def list_ids(self) -> list[str]:
        with self._lock:
            return sorted(self._values)
