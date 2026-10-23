"""PostgreSQL-backed, REST-first FlossWare Memory service."""
import hashlib
import hmac
import json
import os
from contextlib import asynccontextmanager
from uuid import uuid4

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response
from pydantic import BaseModel, Field
from psycopg.rows import dict_row

DB_URL = os.getenv("MEMORY_DATABASE_URL", "postgresql://localhost/flossware_memory")
PROJECT_TOKENS = json.loads(os.getenv("MEMORY_PROJECT_TOKENS", "{}"))
ADMIN_TOKEN = os.getenv("MEMORY_ADMIN_TOKEN", "")

DDL = """
CREATE TABLE IF NOT EXISTS memory_records (
 id TEXT PRIMARY KEY, project_id TEXT NOT NULL,
 scope_type TEXT NOT NULL CHECK (scope_type IN ('global','project','session_task')),
 scope_id TEXT NOT NULL, content TEXT NOT NULL,
 metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
 provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
 revision BIGINT NOT NULL DEFAULT 1,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 CHECK (scope_type <> 'project' OR scope_id = project_id),
 CHECK (scope_type <> 'global' OR scope_id = 'global')
);
CREATE INDEX IF NOT EXISTS memory_records_project_updated ON memory_records(project_id, updated_at DESC, id);
CREATE INDEX IF NOT EXISTS memory_records_fts ON memory_records USING GIN (to_tsvector('simple', content));
CREATE TABLE IF NOT EXISTS memory_idempotency (
 project_id TEXT NOT NULL, idem_key TEXT NOT NULL, request_hash TEXT NOT NULL, memory_id TEXT NOT NULL,
 PRIMARY KEY(project_id, idem_key)
);
"""

def db():
    return psycopg.connect(DB_URL, row_factory=dict_row)

@asynccontextmanager
async def lifespan(app):
    with db() as conn:
        conn.execute(DDL)
    yield

app = FastAPI(title="FlossWare Memory", version="0.1", lifespan=lifespan)

class Write(BaseModel):
    id: str | None = Field(default=None, min_length=1, max_length=512)
    content: str
    scope_type: str = "project"
    scope_id: str | None = None
    metadata: dict = Field(default_factory=dict)
    provenance: dict = Field(default_factory=dict)

def project_context(authorization: str | None = Header(default=None), x_project_id: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer ") or not x_project_id:
        raise HTTPException(401, detail={"code":"unauthorized","message":"Bearer token and X-Project-Id are required"})
    token = authorization[7:]
    if ADMIN_TOKEN and hmac.compare_digest(token, ADMIN_TOKEN):
        return x_project_id
    expected = PROJECT_TOKENS.get(x_project_id)
    if not expected or not hmac.compare_digest(str(expected), token):
        raise HTTPException(403, detail={"code":"project_forbidden","message":"Token is not authorized for this project"})
    return x_project_id

def row_out(row):
    return {"id":row["id"],"content":row["content"],"scope":{"type":row["scope_type"],"id":row["scope_id"]},
            "metadata":row["metadata"],"provenance":row["provenance"],"revision":row["revision"],
            "created_at":row["created_at"],"updated_at":row["updated_at"]}

def visible_clause():
    return "(project_id=%s OR scope_type='global')"

@app.get("/health")
def health():
    return {"status":"ok"}

@app.get("/ready")
def ready():
    try:
        with db() as conn:
            conn.execute("SELECT 1")
        return {"status":"ready","storage":"postgresql"}
    except Exception:
        raise HTTPException(503, detail={"code":"storage_unavailable","message":"PostgreSQL is unavailable"})

@app.post("/api/v1/memories")
def put_memory(body: Write, project: str = Depends(project_context), idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=255), authorization: str | None = Header(default=None)):
    scope_type = body.scope_type
    scope_id = body.scope_id
    if scope_type not in ("global","project","session_task"):
        raise HTTPException(422, detail={"code":"invalid_scope","message":"Unsupported scope type"})
    if scope_type == "global":
        if not ADMIN_TOKEN or not authorization or not hmac.compare_digest(authorization[7:] if authorization.startswith("Bearer ") else "", ADMIN_TOKEN):
            raise HTTPException(403, detail={"code":"global_scope_forbidden","message":"Global scope requires administrative authorization"})
        scope_id = "global" if scope_id is None else scope_id
        if scope_id != "global":
            raise HTTPException(422, detail={"code":"invalid_scope","message":"Global scope id must be global"})
    elif scope_type == "project":
        if scope_id not in (None, project):
            raise HTTPException(403, detail={"code":"cross_project_scope","message":"Project scope must match authenticated project"})
        scope_id = project
    elif not scope_id:
        raise HTTPException(422, detail={"code":"invalid_scope","message":"session_task scope requires an id"})
    memory_id = body.id or str(uuid4())
    material = json.dumps({"id":memory_id,"content":body.content,"scope_type":scope_type,"scope_id":scope_id,"metadata":body.metadata,"provenance":body.provenance}, sort_keys=True, separators=(",",":"))
    digest = hashlib.sha256(material.encode()).hexdigest()
    with db() as conn:
        inserted = conn.execute("INSERT INTO memory_idempotency(project_id,idem_key,request_hash,memory_id) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING", (project,idempotency_key,digest,memory_id)).rowcount
        if not inserted:
            old = conn.execute("SELECT request_hash,memory_id FROM memory_idempotency WHERE project_id=%s AND idem_key=%s", (project,idempotency_key)).fetchone()
            if old["request_hash"] != digest:
                raise HTTPException(409, detail={"code":"idempotency_conflict","message":"Idempotency-Key reused with different content"})
            row = conn.execute("SELECT * FROM memory_records WHERE id=%s AND "+visible_clause(), (old["memory_id"],project)).fetchone()
            if not row:
                raise HTTPException(409, detail={"code":"idempotency_target_missing","message":"Original result no longer exists"})
            return Response(content=json.dumps(row_out(row), default=str), media_type="application/json", status_code=200)
        conn.execute("""INSERT INTO memory_records(id,project_id,scope_type,scope_id,content,metadata,provenance)
          VALUES(%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb)
          ON CONFLICT(id) DO UPDATE SET content=EXCLUDED.content, metadata=EXCLUDED.metadata, provenance=EXCLUDED.provenance,
          scope_type=EXCLUDED.scope_type, scope_id=EXCLUDED.scope_id, revision=memory_records.revision+1, updated_at=now()
          WHERE memory_records.project_id=EXCLUDED.project_id""",
          (memory_id,project,scope_type,scope_id,body.content,json.dumps(body.metadata),json.dumps(body.provenance)))
        row = conn.execute("SELECT * FROM memory_records WHERE id=%s AND project_id=%s", (memory_id,project)).fetchone()
        if not row:
            raise HTTPException(409, detail={"code":"memory_id_conflict","message":"Memory ID belongs to another project"})
    return row_out(row)

@app.get("/api/v1/memories/{memory_id}")
def get_memory(memory_id: str, project: str = Depends(project_context)):
    with db() as conn:
        row = conn.execute("SELECT * FROM memory_records WHERE id=%s AND "+visible_clause(), (memory_id,project)).fetchone()
    if not row:
        raise HTTPException(404, detail={"code":"memory_not_found","message":"Memory record not found"})
    return row_out(row)

@app.get("/api/v1/memories")
def list_memories(offset: int = Query(0,ge=0), limit: int = Query(100,ge=1,le=1000), project: str = Depends(project_context)):
    with db() as conn:
        total = conn.execute("SELECT count(*) AS n FROM memory_records WHERE "+visible_clause(), (project,)).fetchone()["n"]
        rows = conn.execute("SELECT * FROM memory_records WHERE "+visible_clause()+" ORDER BY updated_at DESC,id ASC OFFSET %s LIMIT %s", (project,offset,limit)).fetchall()
    return {"items":[row_out(r) for r in rows],"total":total,"offset":offset,"limit":limit,"next_offset":offset+len(rows) if offset+len(rows)<total else None}

@app.get("/api/v1/memories/export")
def export_memories(offset: int = Query(0,ge=0), limit: int = Query(1000,ge=1,le=1000), project: str = Depends(project_context)):
    return list_memories(offset,limit,project)

@app.get("/api/v1/search")
def search_memories(query: str = Query(min_length=1,max_length=2048), offset: int = Query(0,ge=0), limit: int = Query(20,ge=1,le=100), project: str = Depends(project_context)):
    with db() as conn:
        total = conn.execute("SELECT count(*) AS n FROM memory_records WHERE "+visible_clause()+" AND to_tsvector('simple',content) @@ plainto_tsquery('simple',%s)", (project,query)).fetchone()["n"]
        rows = conn.execute("""SELECT * FROM memory_records WHERE (project_id=%s OR scope_type='global')
          AND to_tsvector('simple',content) @@ plainto_tsquery('simple',%s)
          ORDER BY ts_rank(to_tsvector('simple',content),plainto_tsquery('simple',%s)) DESC,updated_at DESC,id ASC OFFSET %s LIMIT %s""",
          (project,query,query,offset,limit)).fetchall()
    return {"query":query,"items":[row_out(r) for r in rows],"total":total,"offset":offset,"limit":limit,"next_offset":offset+len(rows) if offset+len(rows)<total else None}

@app.delete("/api/v1/memories/{memory_id}", status_code=204)
def delete_memory(memory_id: str, project: str = Depends(project_context)):
    with db() as conn:
        row = conn.execute("DELETE FROM memory_records WHERE id=%s AND project_id=%s RETURNING id", (memory_id,project)).fetchone()
    if not row:
        raise HTTPException(404, detail={"code":"memory_not_found","message":"Memory record not found"})
    return Response(status_code=204)
