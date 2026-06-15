"""
src/ingest.py — Dalla cartella di documenti all'indice vettoriale.

Pipeline: carica i .md  ->  spezza in chunk  ->  embedda  ->  carica su Qdrant.

Le funzioni di caricamento e chunking sono GIÀ pronte (non sono il punto della
challenge). I due passaggi che devi completare tu sono marcati con  # TODO  in
`build_index`: sono il cuore dell'ingestion che hai visto a lezione.
"""
import re
import uuid
from pathlib import Path

import config
from datapizza.modules.splitters import TextSplitter
from datapizza.type import Chunk, DenseEmbedding
from datapizza.vectorstores.qdrant import QdrantVectorstore
from datapizza.core.vectorstore import VectorConfig, Distance


# ── 1. Caricamento del corpus ────────────────────────────────────────────────
def load_corpus() -> dict[str, str]:
    """Ritorna {nome_file: testo} per tutti i .md in data/corpus/."""
    docs = {}
    for path in sorted(Path(config.CORPUS_DIR).glob("*.md")):
        docs[path.name] = path.read_text(encoding="utf-8")
    if not docs:
        raise FileNotFoundError(f"Nessun .md trovato in {config.CORPUS_DIR}")
    return docs


# ── 2. Chunking ──────────────────────────────────────────────────────────────
def _id_chunk(file: str, testo: str) -> str:
    """Id deterministico dal contenuto: reingerire lo stesso chunk lo sovrascrive."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{file}::{testo}"))


def _chunk_naive(file: str, testo: str) -> list[dict]:
    """Chunking 'ingenuo': taglio a caratteri fissi, ignora la struttura."""
    pezzi = TextSplitter(max_char=config.CHUNK_MAX_CHAR,
                         overlap=config.CHUNK_OVERLAP).split(testo)
    return [{"id": _id_chunk(file, c.text), "text": c.text,
             "metadata": {"file": file}} for c in pezzi]


def _chunk_structure_aware(file: str, testo: str) -> list[dict]:
    """Chunking che segue i titoli markdown e NON spezza i blocchi di codice."""
    # Spezza in blocchi (paragrafi e fence di codice), tenendo i ``` atomici.
    blocchi, buf, in_code = [], [], False
    for riga in testo.splitlines():
        if riga.lstrip().startswith("```"):
            in_code = not in_code
        buf.append(riga)
        if not in_code and riga.strip() == "":
            blocchi.append("\n".join(buf).strip()); buf = []
    if buf:
        blocchi.append("\n".join(buf).strip())
    blocchi = [b for b in blocchi if b]

    # Accumula blocchi sotto il titolo corrente fino a max_char, poi flush.
    chunks, corrente, breadcrumb = [], [], file
    def flush():
        if corrente:
            testo_c = "\n\n".join(corrente)
            chunks.append({"id": _id_chunk(file, testo_c), "text": testo_c,
                           "metadata": {"file": file, "breadcrumb": breadcrumb}})
    for b in blocchi:
        if b.startswith("#"):
            breadcrumb = re.sub(r"^#+\s*", "", b.splitlines()[0])
        nuovo = "\n\n".join(corrente + [b])
        if len(nuovo) > config.CHUNK_MAX_CHAR and corrente:
            flush(); corrente = [b]
        else:
            corrente.append(b)
    flush()
    return chunks


def chunk_corpus(docs: dict[str, str]) -> list[dict]:
    fn = _chunk_structure_aware if config.STRUCTURE_AWARE else _chunk_naive
    chunks = []
    for nome, testo in docs.items():
        chunks.extend(fn(nome, testo))
    return chunks


# ── 3. Costruzione dell'indice ───────────────────────────────────────────────
def build_index(embedder) -> QdrantVectorstore:
    """
    Costruisce e ritorna un Qdrant in-memory con tutto il corpus indicizzato.
    Usa embedder.dim per dimensionare la collection: cambiando modello la
    dimensione si adatta da sola (è il classico inghippo "ho cambiato modello
    e Qdrant esplode" — qui è gestito leggendo embedder.dim).
    """
    docs = load_corpus()
    chunks = chunk_corpus(docs)
    print(f"Corpus: {len(docs)} documenti -> {len(chunks)} chunk "
          f"(structure_aware={config.STRUCTURE_AWARE}, max_char={config.CHUNK_MAX_CHAR})")

    # ── TODO 1 · Embedda il testo di tutti i chunk ───────────────────────────
    # Suggerimento: embedder.embed_passages(lista_di_testi) -> lista_di_vettori.
    # Recupera i testi con [c["text"] for c in chunks] e assegna a `vettori`.
    vettori = None  # TODO

    assert vettori is not None and len(vettori) == len(chunks), \
        "TODO 1 non completato: `vettori` deve avere un embedding per chunk."

    # Collection nuova, dimensionata sul modello scelto.
    store = QdrantVectorstore(location=":memory:")
    store.create_collection(
        collection_name=config.COLLECTION,
        vector_config=[VectorConfig(name="dense", dimensions=embedder.dim,
                                    distance=Distance.COSINE)],
    )

    # ── TODO 2 · Carica i chunk su Qdrant ────────────────────────────────────
    # Costruisci un oggetto Chunk per ognuno (id, text, embeddings, metadata) e
    # caricali con store.add(lista, collection_name=config.COLLECTION).
    # L'embedding va passato così: embeddings=[DenseEmbedding(name="dense", vector=v)]
    # TODO

    return store
