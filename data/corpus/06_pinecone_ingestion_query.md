# Pinecone — Ingestion e query

Una volta creato l'index, il giro di lavoro è lo stesso di qualsiasi pipeline RAG: si embeddano i chunk, si caricano i vettori con il loro payload e si interrogano per similarità. Cambiano i nomi delle operazioni e la forma dei dati, non la logica.

## Caricare i vettori con upsert

L'operazione di scrittura si chiama `upsert`, esattamente come in Qdrant, e ha la stessa semantica: se un vettore con quell'`id` esiste già, viene sovrascritto invece di duplicato. Questo rende l'ingestion ripetibile, a patto di generare gli `id` in modo deterministico dal contenuto. In Pinecone ogni vettore porta con sé i metadati nel campo `metadata`, che è l'equivalente del payload di Qdrant.

```python
index = pc.Index("qdrant-docs")

index.upsert(
    vectors=[
        {
            "id": "doc-1",
            "values": embedding,                 # list[float] di lunghezza pari a dimension
            "metadata": {
                "text": "Una collection contiene punti omogenei...",
                "file": "01_concetti_collections.md",
            },
        }
    ],
    namespace="docs",
)
```

Conviene caricare i vettori a batch piuttosto che uno alla volta: una sola chiamata `upsert` con molti vettori è molto più efficiente di molte chiamate da un vettore ciascuna. È buona norma tenere i batch sotto qualche centinaio di vettori per richiesta.

## Interrogare l'index

La ricerca per similarità si fa con `query`: si passa il vettore della domanda, embeddato con lo **stesso modello** usato in ingestion, e il numero di risultati desiderati (`top_k`). Il parametro `include_metadata` chiede a Pinecone di restituire anche il payload, indispensabile per recuperare il testo del chunk e citare la fonte.

```python
risultati = index.query(
    vector=query_embedding,                      # stessa dimensione dell'index
    top_k=5,
    include_metadata=True,
    namespace="docs",
)

for match in risultati["matches"]:
    print(round(match["score"], 4), match["metadata"]["text"][:80])
```

Il campo `score` è la similarità secondo la metrica scelta alla creazione dell'index. Con la metrica coseno il valore tende a `1` per i vettori quasi identici e cala man mano che divergono, come in Qdrant.

## Filtrare sui metadati

Pinecone permette di restringere la ricerca ai soli vettori che soddisfano una condizione sui metadati, passando un `filter` con una sintassi ispirata agli operatori di MongoDB (`$eq`, `$in`, `$gte` e simili). Il filtro si applica durante la ricerca, non dopo: i `top_k` risultati restituiti sono i più vicini *tra quelli che rispettano la condizione*.

```python
risultati = index.query(
    vector=query_embedding,
    top_k=5,
    include_metadata=True,
    filter={"file": {"$eq": "04_deploy_produzione.md"}},
    namespace="docs",
)
```

Questo è l'equivalente del filtraggio sul payload di Qdrant, dove la stessa operazione si esprime con un oggetto `Filter` e una `FieldCondition`. In entrambi i sistemi il principio è identico: i metadati salvati in fase di ingestion sono ciò che rende possibile il recupero mirato in fase di query, e vanno quindi progettati pensando alle domande che si vorranno fare.
