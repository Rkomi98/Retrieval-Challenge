"""
solution/retrieve.py — VERSIONE COMPLETA (per il docente).
"""
import config


def retrieve(store, embedder, query: str, k: int | None = None) -> list:
    k = k or config.TOP_K
    # ── TODO risolto ─────────────────────────────────────────────────────────
    q_vec = embedder.embed_query(query)
    risultati = store.search(collection_name=config.COLLECTION,
                             query_vector=q_vec, k=k, vector_name="dense")
    return risultati


def retrieve_filtered(store, embedder, query: str, file: str, k: int | None = None):
    """Bonus risolto: retrieval ristretto a un solo file via filtro sui metadati."""
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    k = k or config.TOP_K
    q_vec = embedder.embed_query(query)
    hits = store.get_client().query_points(
        collection_name=config.COLLECTION,
        query=q_vec, using="dense", limit=k, with_payload=True,
        query_filter=Filter(must=[FieldCondition(key="file", match=MatchValue(value=file))]),
    ).points
    return hits
