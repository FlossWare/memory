# Stored Data Access Contract

## Purpose

The memory service exposes the memory-domain data it actually persists independently of search and derived retrieval mechanisms. Messaging and change-event publication are deferred.

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

## Decorator composition

Stored-data access SHOULD be implementable through composable contract implementations or decorators where appropriate. Decorators MUST preserve direct access to the delegate's authoritative stored data and document observable ordering or failure behavior.

## Acceptance criteria

- A record can be retrieved by ID when search/index services are unavailable.
- Enumeration/export does not depend on search results and covers all supported persisted memory-domain data.
- Exported records preserve stored content and metadata; persisted chunks and vectors preserve identity and source links where available.
- Backends clearly identify unsupported derived representations.
