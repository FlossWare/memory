package org.flossware.memory.storage;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

/** A deliberately simple, process-local store. Data disappears when the instance is discarded. */
public final class RamMemoryStore implements MemoryStore {
    private final ConcurrentMap<String, String> values = new ConcurrentHashMap<>();

    @Override
    public void put(String id, String value) {
        values.put(requireId(id), requireValue(value));
    }

    @Override
    public Optional<String> get(String id) {
        return Optional.ofNullable(values.get(requireId(id)));
    }

    @Override
    public boolean delete(String id) {
        return values.remove(requireId(id)) != null;
    }

    @Override
    public List<String> listIds() {
        List<String> ids = new ArrayList<>(values.keySet());
        ids.sort(String::compareTo);
        return List.copyOf(ids);
    }

    static String requireId(String id) {
        if (id == null || id.isBlank()) {
            throw new IllegalArgumentException("id must not be null or blank");
        }
        return id;
    }

    static String requireValue(String value) {
        if (value == null) {
            throw new IllegalArgumentException("value must not be null");
        }
        return value;
    }
}
