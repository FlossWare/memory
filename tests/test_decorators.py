import tempfile
import unittest
from pathlib import Path

from flossware_memory import FileSystemMemoryStore, RamCacheMemoryStore, RamMemoryStore


class RamCacheMemoryStoreTest(unittest.TestCase):
    def test_cache_reads_writes_and_deletes_through_filesystem(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "store"
            with RamCacheMemoryStore(FileSystemMemoryStore(path)) as store:
                store.put("one", "first")
                self.assertEqual("first", store.get("one"))
                store.put("one", "second")
                self.assertEqual("second", store.get("one"))
                self.assertTrue(store.delete("one"))
                self.assertIsNone(store.get("one"))
            with FileSystemMemoryStore(path) as reopened:
                self.assertIsNone(reopened.get("one"))

    def test_cache_reads_existing_delegate_value(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "store"
            with FileSystemMemoryStore(path) as filesystem:
                filesystem.put("existing", "persisted")
            with RamCacheMemoryStore(FileSystemMemoryStore(path)) as store:
                self.assertEqual("persisted", store.get("existing"))

    def test_decorators_can_be_stacked(self):
        with RamCacheMemoryStore(RamCacheMemoryStore(RamMemoryStore())) as store:
            store.put("nested", "value")
            self.assertEqual("value", store.get("nested"))


if __name__ == "__main__":
    unittest.main()
