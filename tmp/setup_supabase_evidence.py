"""
One-time setup script to create the `evidence` table + `match_evidence` RPC
in the Intelli-Credit Supabase project using the REST API.
Run once. Safe to re-run (uses IF NOT EXISTS).
"""
import os, sys
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL or SUPABASE_KEY not set in .env")
    sys.exit(1)

try:
    from supabase import create_client
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print(f"✅ Connected to Supabase: {SUPABASE_URL}")
except Exception as e:
    print(f"ERROR connecting to Supabase: {e}")
    sys.exit(1)

# ── SQL to create pgvector extension + evidence table + match function ──────
SETUP_SQL = """
-- Enable pgvector extension (idempotent)
create extension if not exists vector;

-- Create evidence table for External Intelligence indexing
create table if not exists evidence (
    id            bigserial primary key,
    entity_name   text          not null,
    title         text,
    content       text,
    url           text,
    source        text,
    published_date text,
    tags          text[],
    embedding     vector(384),   -- all-MiniLM-L6-v2 produces 384-dim vectors
    created_at    timestamptz default now()
);

-- Create pgvector similarity search index
create index if not exists evidence_embedding_idx
    on evidence
    using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

-- Create the match_evidence RPC used by evidence_indexer.py
create or replace function match_evidence (
    query_embedding  vector(384),
    match_threshold  float,
    match_count      int,
    target_entity    text
)
returns table (
    id             bigint,
    entity_name    text,
    title          text,
    content        text,
    url            text,
    source         text,
    published_date text,
    tags           text[],
    similarity     float
)
language sql stable
as $$
    select
        id,
        entity_name,
        title,
        content,
        url,
        source,
        published_date,
        tags,
        1 - (embedding <=> query_embedding) as similarity
    from evidence
    where
        entity_name ilike '%' || target_entity || '%'
        and 1 - (embedding <=> query_embedding) > match_threshold
    order by embedding <=> query_embedding
    limit match_count;
$$;
"""

# We need to run raw SQL — use the Supabase postgrest /rpc/exec or pg directly.
# The anon key cannot run DDL through REST. We'll use supabase-py's realtime
# channel or a workaround via the pg_dump RPC if available.
# Best path: use requests to hit the DB directly via Supabase's SQL endpoint.
import requests

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Try Supabase Management API (only works with service_role key or management token)
# With anon key we can still try via RPC if pg_execute is enabled.
# Fallback: print the SQL for manual execution.

print("\n" + "="*60)
print("Supabase DDL cannot be run via the anon key through REST.")
print("Please execute the following SQL in your Supabase SQL Editor:")
print(f"  https://supabase.com/dashboard/project/nwlbcysfnamhdnbzybsk/sql/new")
print("="*60)
print(SETUP_SQL)
print("="*60)

# Test connection by checking if 'evidence' table already exists
try:
    resp = client.table("evidence").select("id").limit(1).execute()
    print("\n✅ 'evidence' table already exists and is accessible!")
    print(f"   Row count sample: {len(resp.data)}")
except Exception as e:
    err_msg = str(e)
    if "does not exist" in err_msg or "relation" in err_msg:
        print("\n⚠️  'evidence' table does NOT exist yet.")
        print("   Please run the SQL above in the Supabase SQL Editor.")
    else:
        print(f"\n⚠️  Table check error: {err_msg}")
        print("   This may be a permissions issue with the anon key.")

print("\nDone.")
