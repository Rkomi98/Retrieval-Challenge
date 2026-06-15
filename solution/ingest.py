"""
solution/ingest.py — VERSIONE COMPLETA (per il docente).
Identica a src/ingest.py ma con i TODO risolti. Non distribuire agli studenti.
"""
import re
import uuid
from pathlib import Path

import config
from datapizza.modules.splitters import TextSplitter
from datapizza.type import Chunk, DenseEmbedding
from datapizza.vectorstores.qdrant import QdrantVectorstore
from datapizza.core.vectorstore import VectorConfig, Distance


def load_corpus() -> dict[str, str]:
    docs = {}
    for path in sorted(Path(config.CORPUS_DIR).glob("*.md")):
        docs[path.name] = path.read_text(encoding="utf-8")
    if not docs:
        raise FileNotFoundError(f"Nessun .md trovato in {config.CORPUS_DIR}")
    return docs


def _id_chunk(file: str, testo: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{file}::{testo}"))


def _chunk_naive(file: str, testo: str) -> list[dict]:
    pezzi = TextSplitter(max_char=config.CHUNK_MAX_CHAR,
                         overlap=config.CHUNK_OVERLAP).split(testo)
    return [{"id": _id_chunk(file, c.text), "text": c.text,
             "metadata": {"file": file}} for c in pezzi]


def _chunk_structure_aware(file: str, testo: str) -> list[dict]:
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


def build_index(embedder) -> QdrantVectorstore:
    docs = load_corpus()
    chunks = chunk_corpus(docs)
    print(f"Corpus: {len(docs)} documenti -> {len(chunks)} chunk "
          f"(structure_aware={config.STRUCTURE_AWARE}, max_char={config.CHUNK_MAX_CHAR})")

    # ── TODO 1 risolto ───────────────────────────────────────────────────────
    vettori = embedder.embed_passages([c["text"] for c in chunks])

    assert vettori is not None and len(vettori) == len(chunks)

    store = QdrantVectorstore(location=":memory:")
    store.create_collection(
        collection_name=config.COLLECTION,
        vector_config=[VectorConfig(name="dense", dimensions=embedder.dim,
                                    distance=Distance.COSINE)],
    )

    # ── TODO 2 risolto ───────────────────────────────────────────────────────
    oggetti = [
        Chunk(id=c["id"], text=c["text"],
              embeddings=[DenseEmbedding(name="dense", vector=v)],
              metadata=c["metadata"])
        for c, v in zip(chunks, vettori)
    ]
    store.add(oggetti, collection_name=config.COLLECTION)

    return store
