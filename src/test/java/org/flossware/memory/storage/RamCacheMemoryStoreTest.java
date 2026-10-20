package org.flossware.memory.storage;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class RamCacheMemoryStoreTest {
    @TempDir Path temporaryDirectory;

    @Test
    void cacheReadsWritesAndDeletesThroughFilesystemDelegate() throws IOException {
        Path directory = temporaryDirectory.resolve("cached");
        FileSystemMemoryStore filesystem = new FileSystemMemoryStore(directory);
        try (MemoryStore store = new RamCacheMemoryStore(filesystem)) {
            store.put("one", "first");
            assertEquals(Optional.of("first"), store.get("one"));
            store.put("one", "second");
            assertEquals(Optional.of("second"), store.get("one"));
            assertTrue(store.delete("one"));
            assertTrue(store.get("one").isEmpty());
        }
        try (MemoryStore reopened = new FileSystemMemoryStore(directory)) {
            assertTrue(reopened.get("one").isEmpty());
        }
    }

    @Test
    void cacheLoadsExistingDelegateValues() throws IOException {
        FileSystemMemoryStore filesystem = new FileSystemMemoryStore(temporaryDirectory.resolve("preloaded"));
        filesystem.put("existing", "persisted");
        try (MemoryStore store = new RamCacheMemoryStore(filesystem)) {
            assertEquals(Optional.of("persisted"), store.get("existing"));
        }
    }

    @Test
    void decoratorsCanBeStacked() throws IOException {
        MemoryStore store = new RamCacheMemoryStore(new RamCacheMemoryStore(new RamMemoryStore()));
        try (store) {
            store.put("nested", "value");
            assertEquals(Optional.of("value"), store.get("nested"));
        }
    }
}
