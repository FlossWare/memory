"""Language-level storage contract for opaque memory payloads."""

from __future__ import annotations

from abc import ABC, abstractmethod


class MemoryStore(ABC):
    """Minimal store for opaque text payloads keyed by caller-supplied IDs.

    Implementations do not interpret payloads or define retrieval/ranking policy.
    """

    @abstractmethod
    def put(self, memory_id: str, value: str) -> None:
        """Create or replace a value."""

    @abstractmethod
    def get(self, memory_id: str) -> str | None:
        """Return a value, or None when the ID is absent."""

    @abstractmethod
    def delete(self, memory_id: str) -> bool:
        """Delete a value and report whether it existed."""

    @abstractmethod
    def list_ids(self) -> list[str]:
        """Return IDs in deterministic sorted order."""

    def close(self) -> None:
        """Release resources owned by this store."""

    def __enter__(self) -> MemoryStore:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()


def validate_id(memory_id: str) -> str:
    if not isinstance(memory_id, str) or not memory_id.strip():
        raise ValueError("memory_id must be a non-empty string")
    return memory_id


def validate_value(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("value must be a string")
    return value
