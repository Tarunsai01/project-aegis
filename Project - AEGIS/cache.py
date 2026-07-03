# cache.py
# Layer 2 of the Aegis pipeline — semantic similarity cache.
#
# Why not a regular cache: a standard key-value cache misses on
# "what's your refund policy?" vs "how do I return something?" —
# different strings, same intent, should return the same answer.
#
# Semantic cache converts queries to meaning vectors and checks
# mathematical similarity. Threshold ≥ 0.85 = same intent = serve
# cached response at $0 cost and <50ms latency.
#
# P&L case: 10k calls/day with 40% repeated intent = 4,000 free responses.
# At $0.002/call that's ~$240/month saved from one layer.

import chromadb
from fastembed import TextEmbedding

# BAAI/bge-small-en-v1.5: ~130MB, ONNX runtime, no PyTorch/CUDA —
# fits comfortably in Render's 512MB free tier
embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

# EphemeralClient: in-memory only, resets on restart —
# fine for Render's free tier ephemeral disk. Swap for
# PersistentClient + a paid Render disk if you need durability.
db = chromadb.EphemeralClient()
collection = db.get_or_create_collection(name="llm_cache")

# 0.85 = tight enough to avoid false hits, loose enough to catch paraphrases
# Tune this down to 0.80 if you want more aggressive cache hits
SIMILARITY_THRESHOLD = 0.85


def get_embedding(text: str) -> list:
    """Converts text to a vector — the numeric fingerprint of its meaning."""
    return list(embedder.embed([text]))[0].tolist()


def check_cache(query: str) -> str | None:
    """
    Looks for a semantically close match in the cache.
    Returns the stored response if found, None if not.
    """
    if collection.count() == 0:
        print("[CACHE] Empty — MISS")
        return None

    query_vector = get_embedding(query)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=1
    )

    # ChromaDB returns L2 distance — lower means closer
    # Convert to 0-1 similarity score for readability
    distance = results["distances"][0][0]
    similarity = 1 - distance

    print(f"[CACHE] Similarity: {round(similarity, 3)} | Threshold: {SIMILARITY_THRESHOLD}")

    if similarity >= SIMILARITY_THRESHOLD:
        print("[CACHE] HIT — $0.000000 API cost")
        return results["documents"][0][0]

    print("[CACHE] MISS — forwarding to router")
    return None


def store_in_cache(query: str, response: str):
    """Stores a query-response pair. Next similar query costs nothing."""
    vector = get_embedding(query)
    collection.add(
        documents=[response],
        embeddings=[vector],
        ids=[str(hash(query))]
    )
    print(f"[CACHE] Entry stored. Total cached: {collection.count()}")
