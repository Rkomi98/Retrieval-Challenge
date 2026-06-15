# Indicizzazione e ricerca approssimata

Questo file spiega come Qdrant riesce a trovare i vettori più simili a una query senza confrontarli tutti uno per uno. È la parte che rende il database vettoriale utilizzabile su milioni di punti, e i suoi parametri sono la leva principale per bilanciare velocità, precisione e consumo di memoria.

## Il problema della ricerca esatta

Trovare i `k` vettori più vicini a una query in modo esatto richiede di calcolare la distanza tra la query e ogni vettore della collection. Questo approccio, detto ricerca brute force, è perfettamente accurato ma scala in modo lineare con il numero di punti. Su poche migliaia di vettori è istantaneo, su decine di milioni diventa proibitivo per un sistema che deve rispondere in tempo reale.

La soluzione adottata da Qdrant, come dalla maggior parte dei database vettoriali, è rinunciare all'esattezza in cambio della velocità. Si parla di ricerca approssimata dei vicini più prossimi, in inglese Approximate Nearest Neighbor. L'idea è restituire vettori quasi sempre corretti, accettando una piccola probabilità di mancare qualche risultato, in cambio di una ricerca ordini di grandezza più veloce.

## Come funziona HNSW

L'algoritmo usato da Qdrant si chiama HNSW, acronimo di Hierarchical Navigable Small World. Costruisce un grafo a più livelli in cui ogni vettore è un nodo collegato ai suoi vicini più prossimi. I livelli superiori sono sparsi e contengono pochi nodi con collegamenti a lungo raggio, mentre i livelli inferiori sono densi e descrivono il vicinato locale in dettaglio.

La ricerca parte dall'alto, naviga rapidamente verso la regione dello spazio in cui si trova la query saltando di nodo in nodo, e scende progressivamente di livello affinando la ricerca. È un meccanismo simile a scorrere prima le grandi città su una mappa e poi zoomare sulla via precisa. Il risultato è che il numero di confronti necessari cresce in modo logaritmico, non lineare, con la dimensione della collection.

## I parametri di HNSW

Il comportamento dell'indice si governa con pochi parametri, impostabili alla creazione della collection.

Il parametro `m` definisce il numero di collegamenti che ogni nodo mantiene verso i suoi vicini. Valori alti producono un grafo più connesso, quindi una ricerca più accurata, ma aumentano il consumo di memoria e il tempo di costruzione dell'indice. Il valore predefinito di `16` è un buon punto di partenza per la maggior parte dei casi.

Il parametro `ef_construct` controlla quanti candidati vengono esaminati mentre si costruisce l'indice. Valori più alti producono un grafo di qualità migliore al prezzo di un'indicizzazione più lenta. Non influisce sulla velocità delle ricerche successive, quindi conviene tenerlo generoso.

```python
from qdrant_client.models import VectorParams, Distance, HnswConfigDiff

client.create_collection(
    collection_name="qdrant_docs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    hnsw_config=HnswConfigDiff(m=16, ef_construct=100),
)
```

### Il parametro ef in fase di ricerca

Mentre `m` ed `ef_construct` si fissano alla costruzione, esiste un parametro che agisce solo durante la query: `ef`, talvolta chiamato `hnsw_ef`. Determina quanti candidati l'algoritmo tiene in considerazione mentre cerca. Alzarlo migliora il richiamo, e cioè la probabilità di trovare i veri vicini più prossimi, al costo di una latenza maggiore. La cosa interessante è che si può regolare a ogni singola query, dosando precisione e velocità in base al contesto.

```python
from qdrant_client.models import SearchParams

hits = client.query_points(
    collection_name="qdrant_docs",
    query=query_embedding,
    limit=5,
    search_params=SearchParams(hnsw_ef=128),
).points
```

## La quantizzazione

Gli embedding occupano molta memoria. Un vettore di `1536` dimensioni in virgola mobile a 32 bit pesa circa sei kilobyte, e un milione di vettori supera quindi i sei gigabyte di sola memoria vettoriale. La quantizzazione comprime i vettori riducendo la precisione con cui sono memorizzati, in cambio di un piccolo calo di accuratezza.

La quantizzazione scalare riduce ogni componente da 32 a 8 bit, dividendo per quattro l'occupazione di memoria con una perdita di qualità quasi impercettibile. È l'opzione più usata e quella consigliata come prima scelta.

La quantizzazione binaria spinge la compressione all'estremo, riducendo ogni componente a un solo bit. Il risparmio è enorme e la ricerca diventa rapidissima, ma la perdita di informazione è significativa e funziona bene solo con modelli di embedding ad alta dimensionalità progettati per tollerarla.

```python
from qdrant_client.models import ScalarQuantization, ScalarQuantizationConfig, ScalarType

client.create_collection(
    collection_name="qdrant_docs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(type=ScalarType.INT8, always_ram=True)
    ),
)
```

Una strategia comune consiste nel tenere i vettori quantizzati in memoria per una prima selezione veloce dei candidati, e poi rivalutare i migliori usando i vettori originali a piena precisione conservati su disco. Questo passaggio, chiamato rescoring, recupera quasi tutta l'accuratezza persa nella compressione.

## Quando l'indice non serve

Su collection molto piccole, dell'ordine di poche migliaia di punti, la ricerca brute force esatta è già abbastanza veloce e ha il vantaggio di essere accurata al cento per cento. Qdrant permette di disattivare HNSW impostando la soglia di indicizzazione, utile quando si sa che la collection resterà piccola o quando si privilegia l'esattezza. Nei notebook didattici, dove i punti sono poche centinaia, la differenza di velocità è irrilevante e ci si concentra sulla correttezza dei risultati.
