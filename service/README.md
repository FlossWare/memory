# FlossWare Memory REST service

REST-first memory service backed by PostgreSQL. It stores opaque content and stored metadata/provenance; direct reads and paginated enumeration do not depend on search. The baseline does not create chunks or embeddings and does not call models or messaging services.

## Run locally

Requires Python 3.10+ and PostgreSQL. From the repository root:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r service/requirements-dev.txt
export MEMORY_DATABASE_URL='postgresql://localhost/flossware_memory'
export MEMORY_PROJECT_TOKENS='{"demo":"replace-with-a-project-specific-secret"}'
export MEMORY_ADMIN_TOKEN='replace-with-a-separate-admin-secret'
uvicorn service.app:app --host 127.0.0.1 --port 8080
```

The service creates its tables and indexes at startup. For production, use a secret manager, TLS, restricted database credentials, and controlled migrations.

## Authentication and isolation

Every request requires `Authorization: Bearer ...` and `X-Project-Id`. `MEMORY_PROJECT_TOKENS` maps each project ID to its own token. The project token is bound to the project; changing the header cannot cross project boundaries. The separate admin token may be used with an explicit project header and is required to write global-scope records. Authenticated project clients can read global records. Session-task records remain owned by the authenticated project.

## Endpoints

- `GET /health`: liveness, independent of PostgreSQL.
- `GET /ready`: checks PostgreSQL and returns 503 when unavailable.
- `POST /api/v1/memories`: create or replace a record; requires `Idempotency-Key`.
- `GET /api/v1/memories/{id}`: retrieve the complete persisted record by ID.
- `GET /api/v1/memories?offset=0&limit=100`: enumerate records visible to the authenticated project, with stable ordering and pagination.
- `GET /api/v1/export?offset=0&limit=1000`: paginated export using the same complete stored-record representation.
- `GET /api/v1/search?query=...`: PostgreSQL lexical full-text search, separate from direct access.
- `DELETE /api/v1/memories/{id}`: delete a record owned by the authenticated project.

Records include content, scope, metadata, provenance, revision, and timestamps. Scope types are `global`, `project`, and `session_task`. Reusing an idempotency key with the same request returns the original result; reusing it with different content returns 409. Cross-project reads appear as 404. Structured errors include a stable `code` and human-readable `message`.

## Example

```sh
curl -H 'Authorization: Bearer replace-with-a-project-specific-secret' \
  -H 'X-Project-Id: demo' -H 'Idempotency-Key: note-001' \
  -H 'Content-Type: application/json' \
  -d '{"id":"note-001","content":"original memory payload","scope_type":"project","metadata":{"kind":"note"},"provenance":{"source":"manual"}}' \
  http://127.0.0.1:8080/api/v1/memories

curl -H 'Authorization: Bearer replace-with-a-project-specific-secret' \
  -H 'X-Project-Id: demo' http://127.0.0.1:8080/api/v1/memories/note-001
```

## Current boundary

This is the initial REST/persistence slice. It stores records and metadata only. Chunks and vectors are exposed only once an implementation actually persists them; they are not fabricated. Export is paginated and does not yet guarantee a single immutable snapshot across concurrent writes. Search can be unavailable without making direct record access dependent on it. Messaging and event publication are deferred.
