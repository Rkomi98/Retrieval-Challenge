# Collections, punti e payload

Questo file approfondisce il modello dei dati di Qdrant. Capire come sono organizzati i dati è il presupposto per progettare una collection sensata, e quindi per ottenere un retrieval di qualità.

## Le collection

Una collection è un contenitore di punti che condividono la stessa configurazione vettoriale. Tutti i punti di una collection hanno vettori della stessa dimensione e vengono confrontati con la stessa metrica di distanza. Questo vincolo non è una limitazione arbitraria, ma il riflesso di un fatto matematico: confrontare vettori prodotti da modelli di embedding diversi, o con dimensionalità diverse, non ha alcun senso geometrico.

### Quando creare più collection

La domanda ricorrente è se separare i dati in più collection o tenerli in una sola con un campo che li distingue nel payload. La regola pratica è semplice. Si usano collection diverse quando i vettori provengono da modelli di embedding diversi, oppure quando i requisiti di accesso e di sicurezza sono distinti. Si resta su una sola collection, distinguendo i dati tramite payload, quando i vettori sono omogenei e l'unica differenza è logica, per esempio la lingua del documento o il progetto di appartenenza.

Tenere tutto in una collection e filtrare sul payload è quasi sempre la scelta giusta per un singolo corpus RAG, perché Qdrant è progettato per filtrare in modo efficiente durante la ricerca.

## I punti

Il punto è l'entità elementare di Qdrant. È composto da tre parti: un identificatore univoco, uno o più vettori e un payload.

L'identificatore può essere un intero senza segno oppure un UUID. Conviene derivarlo in modo deterministico dal contenuto del chunk, per esempio con un hash del testo, così che reingerire lo stesso documento sovrascriva il punto esistente invece di crearne uno nuovo. Questo rende la pipeline di ingestion ripetibile.

```python
import hashlib

def chunk_id(file: str, sezione: str, testo: str) -> str:
    raw = f"{file}::{sezione}::{testo}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()
```

### Vettori densi e sparsi

Qdrant gestisce sia vettori densi sia vettori sparsi. Un vettore denso è il classico embedding semantico, un array di numeri in virgola mobile dove ogni dimensione contribuisce al significato. Un vettore sparso ha invece la maggior parte delle componenti a zero e poche posizioni valorizzate, ed è la rappresentazione tipica dei modelli lessicali come BM25 o SPLADE.

La possibilità di tenere entrambi i tipi nello stesso punto è la base della ricerca ibrida, dove il punteggio finale combina la rilevanza semantica del vettore denso con la corrispondenza lessicale del vettore sparso. Nel corso la ricerca ibrida è solo accennata, ma è utile sapere che il modello dei dati la prevede fin dall'inizio.

## Il payload

Il payload è un documento JSON associato al punto. Può contenere stringhe, numeri, booleani, liste e oggetti annidati. Ha due funzioni complementari. La prima è conservare il contenuto che vogliamo restituire al momento del recupero, in primo luogo il testo originale del chunk. La seconda è offrire i campi su cui filtrare la ricerca, per esempio la lingua, la data, il tipo di blocco o l'autore.

```python
payload = {
    "text": "L'indice HNSW costruisce un grafo a più livelli...",
    "file": "02_indicizzazione_hnsw.md",
    "capitolo": "Indicizzazione",
    "sezione": "Come funziona HNSW",
    "tipo_blocco": "paragrafo",
    "lingua": "it",
}
```

Conviene essere parsimoniosi ma precisi nel payload. Ogni campo che pensiamo di usare per filtrare va previsto fin dall'ingestion, perché ricostruirlo dopo significa rifare l'intera indicizzazione. Allo stesso tempo, gonfiare il payload con dati che non servono né alla citazione né al filtro aumenta solo l'occupazione di memoria.

## La metrica di distanza

La metrica si sceglie alla creazione della collection e non si può cambiare in seguito. Qdrant supporta tre metriche principali.

La distanza coseno misura l'angolo tra due vettori e ignora la loro lunghezza. È la scelta corretta per quasi tutti gli embedding testuali moderni, compresi quelli di OpenAI, perché ciò che conta è la direzione del vettore nello spazio semantico, non la sua magnitudine.

Il prodotto scalare tiene conto anche della lunghezza dei vettori. Diventa equivalente al coseno quando i vettori sono normalizzati a norma unitaria, condizione che molti modelli garantiscono già in output.

La distanza euclidea misura la distanza in linea retta tra i due punti nello spazio. È più adatta a embedding dove la magnitudine porta informazione, una situazione rara nel testo ma comune in altri domini.

```python
from qdrant_client.models import VectorParams, Distance

vectors_config = VectorParams(size=1536, distance=Distance.COSINE)
```

La regola operativa è netta: per gli embedding di OpenAI si usa il coseno, e ci si pensa due volte solo se la documentazione del modello dice esplicitamente il contrario.
