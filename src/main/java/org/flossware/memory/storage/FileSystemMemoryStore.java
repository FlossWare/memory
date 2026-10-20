package org.flossware.memory.storage;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.stream.Stream;

/**
 * Stores one UTF-8 payload per file. Writes use a temporary sibling and atomic rename where
 * supported. This implementation is intended for a single process; it does not coordinate
 * concurrent writers in separate processes or detect out-of-band modifications.
 */
public final class FileSystemMemoryStore implements MemoryStore {
    private final Path directory;

    public FileSystemMemoryStore(Path directory) throws IOException {
        if (directory == null) {
            throw new IllegalArgumentException("directory must not be null");
        }
        this.directory = directory.toAbsolutePath().normalize();
        Files.createDirectories(this.directory);
        if (!Files.isDirectory(this.directory)) {
            throw new IOException("Storage path is not a directory: " + this.directory);
        }
    }

    @Override
    public synchronized void put(String id, String value) throws IOException {
        Path target = pathFor(RamMemoryStore.requireId(id));
        byte[] bytes = RamMemoryStore.requireValue(value).getBytes(StandardCharsets.UTF_8);
        Path temporary = Files.createTempFile(directory, ".memory-", ".tmp");
        try {
            Files.write(temporary, bytes);
            try {
                Files.move(temporary, target, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
            } catch (AtomicMoveNotSupportedException unsupported) {
                Files.move(temporary, target, StandardCopyOption.REPLACE_EXISTING);
            }
        } finally {
            Files.deleteIfExists(temporary);
        }
    }

    @Override
    public synchronized Optional<String> get(String id) throws IOException {
        Path path = pathFor(RamMemoryStore.requireId(id));
        if (!Files.exists(path)) {
            return Optional.empty();
        }
        return Optional.of(Files.readString(path, StandardCharsets.UTF_8));
    }

    @Override
    public synchronized boolean delete(String id) throws IOException {
        return Files.deleteIfExists(pathFor(RamMemoryStore.requireId(id)));
    }

    @Override
    public synchronized List<String> listIds() throws IOException {
        List<String> ids = new ArrayList<>();
        try (Stream<Path> paths = Files.list(directory)) {
            paths.filter(Files::isRegularFile)
                 .map(Path::getFileName)
                 .map(Path::toString)
                 .filter(name -> !name.startsWith(".memory-") && name.endsWith(".mem"))
                 .map(name -> name.substring(0, name.length() - 4))
                 .forEach(ids::add);
        }
        ids.sort(String::compareTo);
        return List.copyOf(ids);
    }

    private Path pathFor(String id) {
        // Encode every UTF-8 byte as hex: IDs cannot escape the storage directory.
        byte[] bytes = id.getBytes(StandardCharsets.UTF_8);
        StringBuilder name = new StringBuilder(bytes.length * 2 + 4);
        for (byte value : bytes) {
            name.append(Character.forDigit((value >>> 4) & 0xf, 16));
            name.append(Character.forDigit(value & 0xf, 16));
        }
        Path path = directory.resolve(name + ".mem").normalize();
        if (!path.getParent().equals(directory)) {
            throw new IllegalArgumentException("id resolves outside storage directory");
        }
        return path;
    }
}
