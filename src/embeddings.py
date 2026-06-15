"""
src/embeddings.py — Factory degli embedder.

Tutti gli embedder espongono la STESSA interfaccia, così il resto della pipeline
non sa (e non deve sapere) quale modello c'è sotto:

    .dim                      -> int,  dimensione dei vettori prodotti
    .embed_passages(testi)    -> list[list[float]]   (usato in ingestion)
    .embed_query(testo)       -> list[float]          (usato in retrieval)

Perché distinguere passages e query? Alcuni modelli (es. e5) vogliono un prefisso
diverso per i documenti e per le domande. Tenerli separati qui rende il resto del
codice indipendente da questo dettaglio.

Cambiare modello = cambiare la stringa EMBEDDER in config.py. Niente altro.
"""
import os


class _OpenAIEmbedder:
    """Wrapper sull'OpenAIEmbedder di datapizza-ai."""
    dim = 1536

    def __init__(self, model_name: str = "text-embedding-3-small"):
        from datapizza.embedders.openai import OpenAIEmbedder
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise EnvironmentError("Manca OPENAI_API_KEY nel .env (vedi .env.example).")
        self._e = OpenAIEmbedder(api_key=key, model_name=model_name)

    def embed_passages(self, testi: list[str]) -> list[list[float]]:
        return self._e.embed(testi)

    def embed_query(self, testo: str) -> list[float]:
        return self._e.embed(testo)


class _STEmbedder:
    """Wrapper su un modello sentence-transformers locale e gratuito."""

    def __init__(self, model_name: str, dim: int,
                 query_prefix: str = "", passage_prefix: str = ""):
        from sentence_transformers import SentenceTransformer
        self._m = SentenceTransformer(model_name)
        self.dim = dim
        self._qp = query_prefix
        self._pp = passage_prefix

    def embed_passages(self, testi: list[str]) -> list[list[float]]:
        testi = [self._pp + t for t in testi]
        return self._m.encode(testi, normalize_embeddings=True).tolist()

    def embed_query(self, testo: str) -> list[float]:
        return self._m.encode(self._qp + testo, normalize_embeddings=True).tolist()


# Registro: nome in config.py -> come costruire l'embedder.
_REGISTRY = {
    "openai":    lambda: _OpenAIEmbedder(),
    "minilm-en": lambda: _STEmbedder("all-MiniLM-L6-v2", 384),   # SOLO inglese (apposta)
    "minilm-it": lambda: _STEmbedder("paraphrase-multilingual-MiniLM-L12-v2", 384),
    "e5-small":  lambda: _STEmbedder("intfloat/multilingual-e5-small", 384,
                                     query_prefix="query: ", passage_prefix="passage: "),
    "bge-m3":    lambda: _STEmbedder("BAAI/bge-m3", 1024),
}


def get_embedder(name: str):
    if name not in _REGISTRY:
        raise ValueError(
            f"Embedder '{name}' sconosciuto. Scegli tra: {list(_REGISTRY)} (in config.py)."
        )
    return _REGISTRY[name]()
