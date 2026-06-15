"""
src/retrieve.py — Data una domanda, recupera i chunk più pertinenti.

Un solo passaggio da completare (# TODO): embeddare la query con lo STESSO
modello usato in ingestion e chiedere a Qdrant i k vicini più prossimi.
"""
import config


def retrieve(store, embedder, query: str, k: int | None = None) -> list:
    """
    Ritorna i `k` chunk più simili alla query (oggetti Chunk con .text e .metadata).
    Se k è None usa config.TOP_K.
    """
    k = k or config.TOP_K

    # ── TODO · Recupero ──────────────────────────────────────────────────────
    # 1) embedda la domanda:        q_vec = embedder.embed_query(query)
    # 2) interroga lo store:        store.search(collection_name=config.COLLECTION,
    #                                            query_vector=q_vec, k=k)
    #    Attenzione: la collection usa un vettore di nome "dense"
    #    -> passa vector_name="dense".
    risultati = None  # TODO

    assert risultati is not None, "TODO non completato: `risultati` è ancora None."
    return risultati


# ── Avanzato (facoltativo) · Retrieval filtrato sui metadati ─────────────────
# Recupera SOLO dai chunk di un certo file. Utile quando sai già la fonte.
# Suggerimento: scendi al client Qdrant con store.get_client().query_points(...)
# passando un query_filter costruito con Filter / FieldCondition / MatchValue.
def retrieve_filtered(store, embedder, query: str, file: str, k: int | None = None):
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    k = k or config.TOP_K
    q_vec = embedder.embed_query(query)
    # TODO (avanzato): costruisci il Filter sul campo metadata 'file' e usalo
    # nella query_points. Per ora ritorna il recupero non filtrato.
    raise NotImplementedError("Sfida bonus: implementa il retrieval filtrato.")
