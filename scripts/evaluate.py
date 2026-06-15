"""
scripts/evaluate.py — Il giudice della challenge. NON si tocca.

Costruisce l'indice con i parametri di config.py, lancia ogni domanda del gold
set e controlla una cosa sola: tra i primi TOP_K risultati c'è almeno un chunk
che viene dal file giusto?

Il punteggio è "hit@k" = quante domande hanno beccato la fonte giusta sul totale.
È una verifica volutamente semplice: la teoria della valutazione del retrieval
(recall, precision, MRR...) la vedremo in una lezione dedicata. Qui serve solo
un numero che salga quando le tue scelte migliorano.

Uso:   python scripts/evaluate.py
"""
import json
import sys
from pathlib import Path

# Rende importabili config.py (nella root) e i moduli di src/.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import config
from embeddings import get_embedder
from ingest import build_index
from retrieve import retrieve


def main():
    print("=" * 70)
    print(f"  EMBEDDER={config.EMBEDDER}  TOP_K={config.TOP_K}  "
          f"max_char={config.CHUNK_MAX_CHAR}  overlap={config.CHUNK_OVERLAP}  "
          f"structure_aware={config.STRUCTURE_AWARE}")
    print("=" * 70)

    embedder = get_embedder(config.EMBEDDER)
    store = build_index(embedder)

    gold = json.loads(Path(config.GOLD_PATH).read_text(encoding="utf-8"))
    print(f"\nGold set: {len(gold)} domande\n")

    # Riportiamo il punteggio a più "profondità": hit@1 (la fonte giusta è
    # arrivata PRIMA?) è la misura più severa e quella dove si vede la qualità
    # del ranking; hit@k è più indulgente. Una sola query per domanda: tagliamo
    # la lista di risultati (già ordinata per similarità) ai primi 1, 2, k.
    livelli = sorted({1, 2, config.TOP_K})
    hits = {k: 0 for k in livelli}

    for i, caso in enumerate(gold, 1):
        attesi = set(caso["fonti"])                 # nomi di file accettabili
        risultati = retrieve(store, embedder, caso["query"], k=config.TOP_K)
        trovati = [r.metadata.get("file") for r in risultati]
        for k in livelli:
            hits[k] += int(any(f in attesi for f in trovati[:k]))
        ok1 = trovati[:1] and trovati[0] in attesi
        print(f"{'✅' if ok1 else '·'} [{i:>2}] {caso['query'][:58]:<58} -> {trovati}")

    n = len(gold)
    print("\n" + "-" * 70)
    for k in livelli:
        etichetta = "  <- punteggio principale (ranking)" if k == 1 else ""
        print(f"  hit@{k} = {hits[k]:>2}/{n}  ({100*hits[k]/n:>3.0f}%){etichetta}")
    print("-" * 70)


if __name__ == "__main__":
    main()
