"""
Embeddings and retrieval storage integration using sentence-transformers and Supabase pgvector.
"""
import os
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Load model globally to avoid reloading overhead per call
try:
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    print(f"Failed to load SentenceTransformer: {e}")
    embedding_model = None

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if supabase_url and supabase_key:
    supabase: Client = create_client(supabase_url, supabase_key)
    print("Successfully connected to Supabase Vector DB.")
else:
    supabase = None
    print("WARNING: Supabase URL or Key not found in environment. Cannot connect to DB.")

def index_evidence(entity_name: str, evidence_list: List[Dict]) -> None:
    """
    Generate embeddings of article content and upsert into Supabase pgvector database.
    """
    if not embedding_model or not supabase:
        print("Embeddings model or Supabase not available. Skipping true indexing.")
        return
        
    texts_to_embed = []
    metadata = []
    
    for item in evidence_list:
        article = item.get("article", {})
        text = f"{article.get('title', '')} {article.get('content', '')}".strip()
        if text:
            texts_to_embed.append(text)
            metadata.append(item)
            
    if not texts_to_embed:
        return
        
    print(f"[INDEXER] Generating embeddings for {len(texts_to_embed)} articles...")
    # Batch encode is 5-10x faster than a loop on CPU
    vectors = embedding_model.encode(texts_to_embed).tolist()
    
    records = []
    for i, vector in enumerate(vectors):
        item = metadata[i]
        article = item.get("article", {})
        records.append({
            "entity_name": entity_name,
            "title": article.get("title", ""),
            "content": article.get("content", ""),
            "url": article.get("url", ""),
            "source": article.get("source", ""),
            "published_date": article.get("date", ""),
            "tags": item.get("tags", []),
            "embedding": vector
        })
        
    if records:
        try:
            # Batch upsert via Supabase Python client
            response = supabase.table("evidence").insert(records).execute()
            print(f"Indexed {len(records)} articles for {entity_name} smoothly in Supabase DB")
        except Exception as e:
            print(f"Failed to insert evidence into Supabase: {e}")

def query_evidence(entity_name: str, query: str, top_k: int = 3) -> List[Dict]:
    """
    Search function to retrieve top k related articles based on pgvector similarity via Postgres RPC.
    """
    if not embedding_model or not supabase:
        print("Database offline. Returning []")
        return []
        
    # Convert arbitrary query into match vector
    query_vector = embedding_model.encode(query).tolist()
    
    try:
        # Call the custom Postgres function we just deployed (`match_evidence`)
        response = supabase.rpc("match_evidence", {
            "query_embedding": query_vector,
            "match_threshold": 0.5,
            "match_count": top_k,
            "target_entity": entity_name
        }).execute()
        
        results = []
        for row in response.data:
            results.append({
                "article": {
                    "title": row.get("title"),
                    "content": row.get("content"),
                    "url": row.get("url"),
                    "source": row.get("source"),
                    "date": row.get("published_date")
                },
                "matched_entity": row.get("entity_name"),
                "tags": row.get("tags", []),
                "search_distance": round(row.get("similarity", 0), 4)
            })
            
        print(f"Vector retrieved {len(results)} most relevant signals from Database.")
        return results
        
    except Exception as e:
        print(f"Failed to query Supabase: {e}")
        return []
