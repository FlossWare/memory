# ADR-0002: Minimal storage backends and composable decorators

- **Status:** Proposed
- **Date:** 2026-10-20

## Decision

Define a minimal storage contract for opaque UTF-8 text payloads keyed by caller-supplied string IDs. Provide self-written RAM and filesystem implementations in both Java and Python. Add a delegating decorator base and a RAM read-through/write-through cache decorator that can wrap any store implementation.

Java example:

```java
MemoryStore store = new RamCacheMemoryStore(new FileSystemMemoryStore(path));
```

Python example:

```python
store = RamCacheMemoryStore(FileSystemMemoryStore("./memory-data"))
```

The language-specific interfaces provide parity for in-process consumers. They are not substitutes for the eventual language-neutral remote service contract.

The filesystem remains authoritative in the cache/filesystem composition. The cache only observes operations made through the decorator and does not detect out-of-band changes.

## Constraints

- No framework, ORM, database, or third-party cache library in these reference backends.
- RAM storage is process-local and ephemeral.
- Filesystem storage writes a temporary sibling and renames it into place where supported. It is intended for single-process use and does not coordinate multiple processes.
- IDs are encoded into filenames, rather than used as paths, so path traversal is prevented.
- Listing returns IDs in deterministic sorted order.
- Decorators delegate lifecycle closure to the wrapped store; the outermost decorator owns the delegate.
- The same behavioral contract is tested against RAM and filesystem implementations in each language.
- Cache writes update the cache only after the delegate write succeeds. Deletes evict cached values. Out-of-band delegate changes are not automatically visible through an existing cache.

## Rationale

These implementations are deliberately small reference backends for local development, tests, and embedded use. They do not define memory retrieval/ranking policy and are not substitutes for the eventual PostgreSQL-backed service. Keeping Java and Python implementations behaviorally aligned supports both JVM and Python consumers without making either language the service-wide contract.
