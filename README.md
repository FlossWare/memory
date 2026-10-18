# memory

**Reusable memory capabilities for FlossWare applications.**

This repository is intended to provide explicit contracts and implementations for recording, retrieving, and managing application or agent memory.

## Scope

- Memory item and session/context contracts
- Read, write, update, and lifecycle operations
- Retrieval interfaces and metadata
- Pluggable persistence backends
- Provenance, access controls, and retention semantics
- Tests for memory behavior independent of a specific application

## Architectural boundaries

- `storage` provides persistence mechanisms; memory defines memory-specific semantics.
- `knowledge` manages durable, provenance-aware knowledge; memory focuses on remembered state and context. The exact boundary must be documented before overlapping APIs are introduced.
- `loom` and `loom-ai` define execution contracts. Memory is a capability Loom-compatible applications may invoke, not an orchestration runtime.

Do not assume memory must be a standalone service. Define a stable contract first, then support in-process or remote implementations as justified.

## Status

Repository scaffold. No public API should be considered stable until contracts, backend behavior, and tests are present.
