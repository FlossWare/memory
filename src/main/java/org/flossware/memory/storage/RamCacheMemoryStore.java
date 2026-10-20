package org.flossware.memory.storage;

import java.io.IOException;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

/**
 * Read-through/write-through RAM cache decorator. The delegate remains authoritative for writes.
 * Cache coherence is guaranteed only for operations through this decorator; external changes to
 * the delegate are not observed. This decorator owns and closes its delegate.
 */
public final class RamCacheMemoryStore extends DecoratingMemoryStore {
    private final ConcurrentMap<String, String> cache = new ConcurrentHashMap<>();

    public RamCacheMemoryStore(MemoryStore delegate) {
        super(delegate);
    }

    @Override
    public synchronized void put(String id, String value) throws IOException {
        String checkedId = RamMemoryStore.requireId(id);
        String checkedValue = RamMemoryStore.requireValue(value);
        delegate.put(checkedId, checkedValue);
        cache.put(checkedId, checkedValue);
    }

    @Override
    public synchronized Optional<String> get(String id) throws IOException {
        String checkedId = RamMemoryStore.requireId(id);
        String cached = cache.get(checkedId);
        if (cached != null) {
            return Optional.of(cached);
        }
        Optional<String> value = delegate.get(checkedId);
        value.ifPresent(found -> cache.put(checkedId, found));
        return value;
    }

    @Override
    public synchronized boolean delete(String id) throws IOException {
        String checkedId = RamMemoryStore.requireId(id);
        boolean deleted = delegate.delete(checkedId);
        cache.remove(checkedId);
        return deleted;
    }

    @Override
    public synchronized List<String> listIds() throws IOException {
        // The delegate determines membership; cache contents never invent records.
        return delegate.listIds();
    }

    @Override
    public synchronized void close() throws IOException {
        cache.clear();
        super.close();
    }
}
