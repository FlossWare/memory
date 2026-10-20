"""Filesystem backend with safe ID encoding and atomic replacement."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .storage import MemoryStore, validate_id, validate_value


class FileSystemMemoryStore(MemoryStore):
    """One UTF-8 file per value.

    Intended for use by one process. Atomic replacement is used where the platform
    provides it; separate-process coordination and out-of-band change detection
    are deliberately out of scope.
    """

    def __init__(self, directory: str | os.PathLike[str]) -> None:
        self._directory = Path(directory).expanduser().resolve()
        self._directory.mkdir(parents=True, exist_ok=True)
        if not self._directory.is_dir():
            raise NotADirectoryError(str(self._directory))

    def _path_for(self, memory_id: str) -> Path:
        checked = validate_id(memory_id)
        # IDs are data, never path fragments. Hex encoding prevents traversal and
        # avoids filename portability problems with separators and special chars.
        encoded = checked.encode("utf-8").hex()
        path = (self._directory / f"{encoded}.mem").resolve()
        if path.parent != self._directory:
            raise ValueError("memory ID resolves outside storage directory")
        return path

    def put(self, memory_id: str, value: str) -> None:
        target = self._path_for(memory_id)
        data = validate_value(value).encode("utf-8")
        fd, temporary_name = tempfile.mkstemp(prefix=".memory-", suffix=".tmp", dir=self._directory)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_name, target)
        finally:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass

    def get(self, memory_id: str) -> str | None:
        path = self._path_for(memory_id)
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None

    def delete(self, memory_id: str) -> bool:
        try:
            self._path_for(memory_id).unlink()
            return True
        except FileNotFoundError:
            return False

    def list_ids(self) -> list[str]:
        ids: list[str] = []
        for path in self._directory.glob("*.mem"):
            try:
                encoded = path.name[:-4]
                memory_id = bytes.fromhex(encoded).decode("utf-8")
                if self._path_for(memory_id) == path.resolve():
                    ids.append(memory_id)
            except (ValueError, UnicodeDecodeError):
                # Ignore unrelated or malformed files in the storage directory.
                continue
        return sorted(ids)
