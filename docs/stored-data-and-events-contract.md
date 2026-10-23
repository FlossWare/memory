# Stored Data Access and Change Events Contract

## Purpose

The memory service exposes the memory-domain data it actually persists independently of search and derived retrieval mechanisms. It also publishes domain-change notifications through a technology-neutral publication port, with a no-op implementation available by default.

This document defines intended contract behavior. It does not claim that every current backend already implements every capability.

## Stored-data fidelity

The authoritative source is the data persisted by the selected memory implementation. Search results are not a substitute for stored data.

A conforming implementation SHALL provide stable logical access to persisted memory records and SHALL NOT require a search query, lexical index, vector index, or ranking operation to retrieve a record by its identifier.

The contract SHALL distinguish persisted data from derived representations. Depending on the backend and configured capabilities, persisted data may include:

- Original record content in its stored form.
- Stored record metadata and provenance.
- Persisted chunks, including their IDs, content, ordering/offset information where available, parent-record identity, and source revision where supported.
- Persisted embeddings/vectors and their model identity, dimensions, and links to the represented record or chunk where stored.
- Other memory-domain representations that the implementation persists.

A service SHALL expose the data it actually stores. It SHALL NOT fabricate a representation that is not persisted and present it as stored data. Capability metadata or documentation SHOULD make backend-specific persistence differences discoverable.

## Required access capabilities

The public contract SHOULD support:

1. Get one record by stable ID, including its complete stored content and metadata.
2. Enumerate records with deterministic pagination and documented filtering/order semantics.
3. Retrieve persisted chunks and other representations by stable identity and/or parent record.
4. Retrieve stored embedding values and associated metadata when embeddings are persisted.
5. Export all supported persisted memory-domain data without relying on search or ranking.
6. Preserve resource identity and available lineage across reads and exports.

Bulk export SHOULD define a consistent snapshot or explicitly document its consistency boundary. Export formats and pagination tokens SHOULD be documented and suitable for large datasets. A complete export MUST include every persisted memory-domain record and representation covered by the export contract, not merely records returned by a search.

A backend that does not persist chunks or embeddings can still conform to the core record-access contract. It SHALL report that those representations are unsupported or absent rather than silently creating them during a stored-data read.

## Search is a separate capability

Text search, semantic vector search, hybrid search, ranking, summaries, and retrieval policies are separate capabilities. They MAY use derived indexes and representations.

A stale, unavailable, or rebuilding search index SHALL NOT make an otherwise persisted record inaccessible through direct retrieval or complete enumeration/export. Search MAY be temporarily degraded while stored-data access remains available.

## Domain change publication

The memory service SHALL define and invoke a technology-neutral publication port for successful domain state changes. A no-op publisher SHALL be available and MAY be the default. Core memory operations SHALL not require a deployed broker or messaging service.

Initial event types SHOULD include:

- `memory.record.created`
- `memory.record.updated`
- `memory.record.deleted`

Events SHALL identify the record and the change; include an event ID, event type, envelope version, occurrence time, producer identity, and record revision where available; and carry a schema-defined payload. Event payloads SHOULD remain compact and avoid copying large content unless the event contract explicitly requires it. Consumers can fetch the full persisted record through the stored-data API.

The publisher call SHALL occur only after the relevant state transition has succeeded. A no-op publisher SHALL preserve ordinary operation behavior. A future real publisher MUST document delivery and failure semantics. If losing a notification is unacceptable, a durable outbox or equivalent mechanism SHOULD be considered rather than claiming that an ordinary post-write publish is atomic.

Events are notifications, not the source of truth. Consumers SHALL tolerate duplicates and SHOULD support reconciliation through direct access or export. The event contract does not currently promise durable delivery, replay, global ordering, or exactly-once processing.

## Decorator composition

Stored-data access and event publication SHOULD be implementable as composable contract implementations or decorators where appropriate. For example, an event-publishing decorator can delegate to a storage implementation, then publish the successful change without coupling the storage implementation to a broker.

Decorator order and failure semantics MUST be documented where they affect observable behavior. A decorator SHALL NOT claim stronger persistence/publication atomicity than its underlying implementation provides.

## Acceptance criteria

- A record can be retrieved by ID when search/index services are unavailable.
- Enumeration/export does not depend on search results and covers all supported persisted memory-domain data.
- Exported records preserve stored content and metadata; persisted chunks and vectors preserve identity and source links where available.
- Backends clearly identify unsupported derived representations.
- Successful create/update/delete operations invoke the publication port with the appropriate event; failed state changes do not announce a successful change.
- The no-op publisher requires no external infrastructure and does not change operation outcomes.
- Tests verify duplicate-safe event identity and record-fetch follow-up behavior where those fields are supported.
