import tempfile
import unittest
from pathlib import Path

from flossware_memory import FileSystemMemoryStore, RamMemoryStore


class MemoryStoreContract:
    def assert_store_contract(self, store):
        with store:
            self.assertIsNone(store.get("missing"))
            store.put("b", "first")
            self.assertEqual("first", store.get("b"))
            store.put("b", "updated")
            self.assertEqual("updated", store.get("b"))
            store.put("a", "another")
            self.assertEqual(["a", "b"], store.list_ids())
            self.assertTrue(store.delete("b"))
            self.assertFalse(store.delete("b"))
            self.assertIsNone(store.get("b"))
            self.assertEqual(["a"], store.list_ids())


class RamMemoryStoreTest(MemoryStoreContract, unittest.TestCase):
    def test_contract(self):
        self.assert_store_contract(RamMemoryStore())


class FileSystemMemoryStoreTest(MemoryStoreContract, unittest.TestCase):
    def test_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assert_store_contract(FileSystemMemoryStore(Path(directory) / "store"))

    def test_persists_between_instances(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "store"
            with FileSystemMemoryStore(path) as store:
                store.put("note", "persisted")
            with FileSystemMemoryStore(path) as store:
                self.assertEqual("persisted", store.get("note"))

    def test_ids_are_not_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "store"
            with FileSystemMemoryStore(root) as store:
                store.put("../../outside", "safe")
                self.assertEqual("safe", store.get("../../outside"))
            self.assertFalse((Path(directory) / "outside").exists())


if __name__ == "__main__":
    unittest.main()
