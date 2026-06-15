# Pinecone — Concetti di base

Pinecone è un database vettoriale gestito (managed) erogato come servizio cloud. A differenza di Qdrant, che è open source e si può eseguire in locale o su una macchina propria, Pinecone non si installa: si usa attraverso un'API, e l'infrastruttura che conserva e indicizza i vettori è gestita interamente dal fornitore. Questo sposta il compromesso classico tra controllo e operatività: con Pinecone non si amministra alcun server, ma si dipende da un servizio esterno e dal suo modello di costo.

## Index e namespace

L'unità organizzativa principale in Pinecone è l'**index**. Un index conserva vettori della stessa dimensione e usa un'unica metrica di distanza, esattamente come una collection in Qdrant. La dimensione e la metrica si fissano alla creazione e non si possono cambiare dopo: per usare un altro modello di embedding con dimensione diversa occorre creare un nuovo index.

```python
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key="LA_TUA_API_KEY")

pc.create_index(
    name="qdrant-docs",
    dimension=1536,                     # deve combaciare col modello di embedding
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
)
```

All'interno di un singolo index, i vettori possono essere partizionati in **namespace**. Un namespace è una suddivisione logica: le query vengono eseguite all'interno di un namespace alla volta, e questo permette di tenere separati insiemi di dati diversi (per esempio i documenti di clienti distinti) senza creare un index per ciascuno. Se non si specifica nulla, i vettori finiscono nel namespace di default, identificato da una stringa vuota.

## Serverless e pod-based

Pinecone offre due modalità di deployment. La modalità **serverless** scala automaticamente con il volume dei dati e si paga in base a quanto si legge, si scrive e si conserva: non si dimensiona alcuna macchina in anticipo, ed è la scelta predefinita per la maggior parte dei nuovi progetti. La modalità **pod-based**, più vecchia, alloca risorse di calcolo fisse (i pod) che si pagano a ore indipendentemente dall'uso: dà un controllo più fine sulle prestazioni ma richiede di stimare la capacità in anticipo.

Per l'esercitazione e per i progetti di piccola scala, la modalità serverless è quella di riferimento: non richiede scelte di dimensionamento e azzera i costi fissi quando l'index è inattivo.

## Metrica di distanza

Come in Qdrant, la metrica va scelta in coerenza con il modello di embedding. Per gli embedding di OpenAI `text-embedding-3-small`, normalizzati, la metrica naturale è il coseno (`cosine`). Pinecone supporta anche il prodotto scalare (`dotproduct`) e la distanza euclidea (`euclidean`); usare una metrica incoerente con il modello produce risultati di ricerca di qualità scadente, anche quando il codice gira senza errori.

## Quando ha senso

Pinecone è adatto a chi vuole arrivare in produzione senza gestire infrastruttura: niente container da avviare, niente storage da amministrare, scalabilità delegata al fornitore. Il prezzo di questa comodità è il vincolo a un servizio esterno e un modello di costo a consumo che va monitorato. Qdrant, all'opposto, lascia il pieno controllo a fronte di un onere operativo maggiore. La scelta tra i due dipende più dal contesto del team che dalle differenze tecniche, che a livello di concetti — vettori, dimensione, metrica, filtri sui metadati — sono in larga parte sovrapponibili.
