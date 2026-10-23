# memory

**Reusable memory capabilities for FlossWare applications.**

This repository provides small storage contracts and implementations for recording and retrieving opaque memory payloads. Storage is a backend concern, not the memory retrieval/ranking policy or an orchestration runtime.

## Initial storage implementations

Both Java and Python implementations provide the same minimal operations:

- `put(id, value)`: create or replace a UTF-8 text payload
- `get(id)`: return the payload or an explicit absent result
- `delete(id)`: delete a payload and report whether it existed
- `listIds()` / `list_ids()`: list IDs in deterministic sorted order

| Capability | Java | Python |
| --- | --- | --- |
| RAM backend | `RamMemoryStore` | `RamMemoryStore` |
| Filesystem backend | `FileSystemMemoryStore` | `FileSystemMemoryStore` |
| Decorator base | `DecoratingMemoryStore` | `DecoratingMemoryStore` |
| RAM cache decorator | `RamCacheMemoryStore` | `RamCacheMemoryStore` |

The RAM backend is process-local and ephemeral. Filesystem backends store one payload per file, encode IDs rather than treating them as paths, and atomically replace files where the platform supports it. Filesystem implementations are intended for single-process use and do not coordinate independent writers.

### Java

Java 25+, Maven:

```java
MemoryStore store = new RamCacheMemoryStore(
    new FileSystemMemoryStore(Path.of("./memory-data"))
);
try (store) {
    store.put("session-1", "remember this");
    String value = store.get("session-1").orElseThrow();
}
```

Run tests with `mvn test`.

### Python

Python 3.10+, standard-library runtime, installable with pip:

```python
from flossware_memory import FileSystemMemoryStore, RamCacheMemoryStore

with RamCacheMemoryStore(FileSystemMemoryStore("./memory-data")) as store:
    store.put("session-1", "remember this")
    value = store.get("session-1")
```

Run tests with `python -m unittest discover -s tests`.

### Decorator semantics

The filesystem store remains authoritative in a RAM-cache/filesystem composition. The cache is read-through and write-through; puts update it only after the delegate write succeeds, and deletes evict cached values. Cache coherence applies to operations through the decorator. Changes made directly to the delegate are not observed by an existing cache. The outermost decorator owns and closes its delegate.

## REST service

See [service/README.md](service/README.md) for the initial PostgreSQL-backed REST service, direct record retrieval, pagination, export, and lexical search. Messaging is deferred.

## Stored-data access contract

See [Stored Data Access Contract](docs/stored-data-and-events-contract.md) for direct access, representation fidelity, and complete paginated export requirements. Search is a separate capability.

## Architectural boundaries

- Storage provides persistence mechanisms; memory defines memory-specific semantics.
- Knowledge manages durable, provenance-aware knowledge; memory focuses on remembered state and context. Document the boundary before introducing overlapping APIs.
- Loom and loom-ai define execution contracts. Memory is a capability Loom-compatible applications may invoke, not an orchestration runtime.
- The Java interface and Python protocol are implementation-level contracts. A language-neutral REST contract remains necessary for remote consumers; MCP and future protocol adapters should reuse the same service behavior.

## Status

The initial RAM/filesystem backends and decorator examples are being established as reference implementations. The wider memory API, retrieval behavior, service deployment, and durable database backend remain separate work.
