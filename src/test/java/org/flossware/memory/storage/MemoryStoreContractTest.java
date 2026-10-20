package org.flossware.memory.storage;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class MemoryStoreContractTest {
    @TempDir Path temporaryDirectory;

    @Test
    void ramStoreSupportsBasicOperations() throws IOException {
        assertContract(new RamMemoryStore());
    }

    @Test
    void filesystemStoreSupportsBasicOperations() throws IOException {
        assertContract(new FileSystemMemoryStore(temporaryDirectory.resolve("store")));
    }

    @Test
    void filesystemStorePersistsAcrossInstances() throws IOException {
        Path directory = temporaryDirectory.resolve("persistent");
        try (MemoryStore first = new FileSystemMemoryStore(directory)) {
            first.put("note-1", "hello");
        }
        try (MemoryStore second = new FileSystemMemoryStore(directory)) {
            assertEquals(Optional.of("hello"), second.get("note-1"));
        }
    }

    @Test
    void filesystemIdsCannotTraverseDirectories() throws IOException {
        MemoryStore store = new FileSystemMemoryStore(temporaryDirectory.resolve("safe"));
        assertDoesNotThrow(() -> store.put("../../outside", "safe payload"));
        assertEquals(Optional.of("safe payload"), store.get("../../outside"));
        assertFalse(FilesExist(temporaryDirectory.resolve("outside")));
    }

    private static boolean FilesExist(Path path) {
        return java.nio.file.Files.exists(path);
    }

    private static void assertContract(MemoryStore store) throws IOException {
        try (store) {
            assertTrue(store.get("missing").isEmpty());
            store.put("b", "first");
            assertEquals(Optional.of("first"), store.get("b"));
            store.put("b", "updated");
            assertEquals(Optional.of("updated"), store.get("b"));
            store.put("a", "another");
            assertEquals(List.of("a", "b"), store.listIds());
            assertTrue(store.delete("b"));
            assertFalse(store.delete("b"));
            assertTrue(store.get("b").isEmpty());
            assertEquals(List.of("a"), store.listIds());
        }
    }
}
