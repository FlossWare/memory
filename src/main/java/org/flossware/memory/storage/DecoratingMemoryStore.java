package org.flossware.memory.storage;

import java.io.IOException;
import java.util.List;
import java.util.Optional;
import java.util.Objects;

/** Base decorator that delegates the storage contract to another store. */
public abstract class DecoratingMemoryStore implements MemoryStore {
    protected final MemoryStore delegate;

    protected DecoratingMemoryStore(MemoryStore delegate) {
        this.delegate = Objects.requireNonNull(delegate, "delegate");
    }

    @Override
    public void put(String id, String value) throws IOException {
        delegate.put(id, value);
    }

    @Override
    public Optional<String> get(String id) throws IOException {
        return delegate.get(id);
    }

    @Override
    public boolean delete(String id) throws IOException {
        return delegate.delete(id);
    }

    @Override
    public List<String> listIds() throws IOException {
        return delegate.listIds();
    }

    @Override
    public void close() throws IOException {
        delegate.close();
    }
}
