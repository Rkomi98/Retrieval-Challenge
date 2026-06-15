# Filtri sul payload e ricerca condizionata

Questo file spiega come restringere la ricerca a un sottoinsieme di punti usando i campi del payload. È una funzionalità centrale per il RAG, perché spesso non basta trovare i chunk semanticamente vicini: serve trovarli all'interno di un certo documento, di una certa lingua o di un certo intervallo di date.

## Perché filtrare

Immaginiamo una collection che contiene la documentazione di più progetti. Una query semantica pura potrebbe restituire chunk pertinenti ma appartenenti al progetto sbagliato. Filtrando sul campo `progetto` del payload, si vincola la ricerca a restituire solo punti che soddisfano la condizione, mantenendo comunque l'ordinamento per similarità all'interno del sottoinsieme.

Qdrant esegue il filtro durante la navigazione del grafo HNSW, non dopo. Questo è importante: significa che il filtro non si limita a scartare i risultati a posteriori, rischiando di restituire meno di `k` punti, ma guida la ricerca verso le regioni dello spazio che soddisfano la condizione. Il meccanismo si chiama filtraggio durante la ricerca e dipende dalla presenza di un indice sul payload.

## La struttura di un filtro

Un filtro si compone di clausole combinate con tre operatori logici. La clausola `must` richiede che tutte le condizioni siano vere ed equivale a una congiunzione logica. La clausola `should` premia i punti che soddisfano almeno una condizione e funziona come una disgiunzione. La clausola `must_not` esclude i punti che soddisfano la condizione e agisce da negazione.

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

filtro = Filter(
    must=[
        FieldCondition(key="lingua", match=MatchValue(value="it")),
        FieldCondition(key="tipo_blocco", match=MatchValue(value="paragrafo")),
    ]
)
```

### Match esatto e match su liste

La condizione `MatchValue` verifica l'uguaglianza esatta con un valore. Quando il campo del payload contiene una lista, il match è soddisfatto se il valore cercato è presente tra gli elementi. Per cercare uno tra più valori possibili si usa `MatchAny`, che corrisponde a un'appartenenza a un insieme.

```python
from qdrant_client.models import MatchAny

filtro = Filter(
    must=[
        FieldCondition(key="file", match=MatchAny(any=["01_concetti_collections.md", "02_indicizzazione_hnsw.md"]))
    ]
)
```

### Condizioni su intervalli

Per i campi numerici, comprese le date convertite in timestamp, si usa la condizione `Range`, che accetta i limiti `gt`, `gte`, `lt` e `lte`. Permette di selezionare punti il cui valore cade in un intervallo, per esempio i documenti aggiornati dopo una certa data.

```python
from qdrant_client.models import Range

filtro = Filter(
    must=[
        FieldCondition(key="anno", range=Range(gte=2024, lte=2026))
    ]
)
```

## Applicare il filtro alla ricerca

Il filtro si passa alla query insieme al vettore. La ricerca restituirà i punti più simili tra quelli che soddisfano la condizione.

```python
hits = client.query_points(
    collection_name="qdrant_docs",
    query=query_embedding,
    query_filter=filtro,
    limit=5,
    with_payload=True,
).points
```

## L'indice sul payload

Perché il filtraggio durante la ricerca sia efficiente, il campo su cui si filtra deve essere indicizzato. Senza indice, Qdrant è comunque in grado di applicare il filtro, ma deve scorrere i punti e le prestazioni degradano sulle collection grandi. Creare l'indice è un'operazione esplicita che si fa una volta sola per ciascun campo.

```python
from qdrant_client.models import PayloadSchemaType

client.create_payload_index(
    collection_name="qdrant_docs",
    field_name="lingua",
    field_schema=PayloadSchemaType.KEYWORD,
)
```

Il tipo di schema va scelto in base alla natura del campo. `KEYWORD` è adatto alle stringhe usate come etichette, `INTEGER` e `FLOAT` ai numeri, `DATETIME` alle date, `GEO` alle coordinate geografiche. Indicizzare i campi giusti fin dall'ingestion è una delle scelte che più incidono sulle prestazioni di un sistema RAG in produzione.

## Filtri e qualità del recupero

Vale la pena ricordare che il filtro agisce sul recupero, non sulla rilevanza semantica. Un filtro troppo stretto può svuotare il sottoinsieme di ricerca al punto da non restituire nulla di utile, mentre un filtro assente lascia che chunk fuori contesto competano con quelli giusti. La progettazione dei campi di payload e dei filtri è parte integrante della fase di ingestion, non un dettaglio successivo: i metadati che non vengono salvati al momento dell'inserimento non potranno mai essere usati per filtrare in seguito.
