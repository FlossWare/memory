package org.flossware.memory.storage;

import java.io.IOException;
import java.util.List;
import java.util.Optional;

/**
 * Minimal storage contract for opaque UTF-8 memory payloads keyed by caller-supplied IDs.
 * Implementations do not interpret payloads or provide retrieval/ranking policy.
 */
public interface MemoryStore extends AutoCloseable {
    void put(String id, String value) throws IOException;

    Optional<String> get(String id) throws IOException;

    boolean delete(String id) throws IOException;

    List<String> listIds() throws IOException;

    /** Releases resources owned by this store. Simple stores need not own any. */
    @Override
    default void close() throws IOException {
        // No resources by default.
    }
}
