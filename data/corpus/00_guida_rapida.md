# Qdrant — Guida rapida per l'esercitazione

Questo documento è il punto di partenza per la challenge di Blocco 2. Serve a mettere in piedi un'istanza di Qdrant in pochi minuti, creare la prima collection e fare il primo inserimento e la prima ricerca. Gli altri file della cartella (`01_concetti_collections.md`, `02_indicizzazione_hnsw.md`, `03_filtering_payload.md`, `04_deploy_produzione.md`) approfondiscono i temi che qui vengono solo sfiorati.

Qdrant è un database vettoriale open source scritto in Rust. Conserva vettori ad alta dimensionalità insieme a un payload arbitrario in formato JSON, e permette di recuperare i vettori più simili a una query secondo una metrica di distanza. È esattamente il componente che, in una pipeline RAG, sta a valle della fase di ingestion: una volta che i documenti sono stati spezzati in chunk ed embeddati, i vettori risultanti vanno indicizzati da qualche parte, e quel posto è il vector database.

## Avviare Qdrant in locale

Il modo più rapido per avere un'istanza funzionante è Docker. L'immagine ufficiale espone la porta `6333` per l'API REST e per il client Python, e la porta `6334` per l'interfaccia gRPC.

```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v "$(pwd)/qdrant_storage:/qdrant/storage" \
    qdrant/qdrant
```

Il flag `-v` monta una cartella locale come storage persistente: senza di esso, fermando il container si perde tutto. Una volta avviato, la dashboard web è raggiungibile su `http://localhost:6333/dashboard` e permette di ispezionare collection e punti senza scrivere codice.

Per l'esercitazione non è obbligatorio avere Qdrant via Docker. Il client Python supporta una modalità in-memory che non richiede alcun server: utile per i notebook didattici, dove l'intero indice vive nel processo Python e svanisce alla chiusura del kernel.

```python
from qdrant_client import QdrantClient

# Server reale in ascolto sulla 6333
client = QdrantClient(host="localhost", port=6333)

# Oppure tutto in memoria, senza server (ideale per i notebook)
client = QdrantClient(location=":memory:")
```

## Creare la prima collection

Una collection è l'unità organizzativa di Qdrant: contiene punti omogenei per dimensione del vettore e metrica di distanza. Per crearla servono due informazioni, la dimensione dei vettori e la distanza con cui confrontarli. Per gli embedding di OpenAI `text-embedding-3-small` la dimensione è `1536` e la metrica naturale è il coseno.

```python
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

client = QdrantClient(location=":memory:")

client.create_collection(
    collection_name="qdrant_docs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)
```

## Inserire i primi punti

Ogni punto è composto da un identificatore, dal vettore e da un payload. Il payload è un dizionario JSON libero: è il posto dove conservare il testo originale del chunk e i metadati che serviranno poi a filtrare e a citare la fonte.

```python
from qdrant_client.models import PointStruct

client.upsert(
    collection_name="qdrant_docs",
    points=[
        PointStruct(
            id=1,
            vector=embedding,                      # list[float] di lunghezza 1536
            payload={
                "text": "Una collection contiene punti omogenei...",
                "file": "01_concetti_collections.md",
                "sezione": "Collections",
            },
        )
    ],
)
```

L'operazione di scrittura si chiama `upsert` e non `insert` di proposito: se un punto con quell'`id` esiste già, viene sovrascritto. Questo rende l'ingestion idempotente, e cioè rieseguibile più volte senza creare duplicati, a patto di generare gli `id` in modo deterministico a partire dal contenuto.

## La prima ricerca

Recuperare i vettori più vicini a una query significa embeddare la query con lo stesso modello usato in ingestion e chiedere a Qdrant i `k` punti più simili. L'API moderna è `query_points`; la vecchia `search` resta disponibile ma è deprecata.

```python
hits = client.query_points(
    collection_name="qdrant_docs",
    query=query_embedding,                         # list[float] di lunghezza 1536
    limit=5,
    with_payload=True,
).points

for h in hits:
    print(round(h.score, 4), h.payload["text"][:80])
```

Il campo `score` riportato per ogni risultato è la similarità secondo la metrica scelta in fase di creazione della collection. Con la distanza coseno il valore tende a `1` per i vettori quasi identici e cala man mano che i vettori divergono.

## Usare il wrapper datapizza-ai

Nel corso lavoriamo con il framework `datapizza-ai`, che incapsula sia l'embedder sia il vector store dietro un'interfaccia comune. La logica resta quella appena vista, ma le chiamate passano per le classi del framework. È questo lo strato che useremo nel notebook dell'esercitazione.

```python
from datapizza.vectorstores.qdrant import QdrantVectorstore
from datapizza.core.vectorstore import VectorConfig, Distance
from datapizza.type import Chunk, DenseEmbedding

store = QdrantVectorstore(location=":memory:")

store.create_collection(
    collection_name="qdrant_docs",
    vector_config=[VectorConfig(name="dense", dimensions=1536, distance=Distance.COSINE)],
)

store.add(
    Chunk(
        id="doc-1",
        text="Una collection contiene punti omogenei...",
        embeddings=[DenseEmbedding(name="dense", vector=embedding)],
        metadata={"file": "01_concetti_collections.md"},
    ),
    collection_name="qdrant_docs",
)

risultati = store.search(collection_name="qdrant_docs", query_vector=query_embedding, k=5)
```

## Prossimi passi

Con questo è possibile completare il giro minimo dell'esercitazione: avviare Qdrant, creare una collection, inserire i chunk embeddati e interrogarli. Per andare oltre, i file successivi spiegano come è fatta davvero una collection, come funziona l'indice HNSW che rende veloce la ricerca, come filtrare sul payload per restringere il recupero e come portare Qdrant in produzione.
