# ADR-0002: Minimal storage backends and composable decorators

- **Status:** Proposed
- **Date:** 2026-10-20

## Decision

Define a small `MemoryStore` contract for opaque UTF-8 payloads keyed by string IDs. Supply self-written RAM and filesystem implementations. Add a base decorator and a RAM read-through/write-through cache decorator that can wrap any `MemoryStore`.

Example:

```java
MemoryStore store = new RamCacheMemoryStore(new FileSystemMemoryStore(path));
```

The filesystem remains authoritative in this composition. The cache only observes operations made through the decorator and does not detect out-of-band changes.

## Constraints

- No framework, ORM, database, or third-party cache library.
- RAM storage is process-local and ephemeral.
- Filesystem storage writes a temporary sibling and renames it into place where supported. It is intended for single-process use and does not coordinate multiple processes.
- IDs are encoded into filenames, rather than used as paths, so path traversal is impossible.
- All implementations return sorted, immutable ID lists.
- Decorators delegate lifecycle closure to the wrapped store; the outermost decorator owns the delegate.
- Contract tests are shared across RAM and filesystem implementations.

## Rationale

These implementations are deliberately small reference backends for local development, tests, and embedded use. They do not define memory retrieval/ranking policy and are not substitutes for the eventual PostgreSQL-backed service.
