# Deploy e gestione in produzione

Questo file raccoglie ciò che serve sapere per portare Qdrant oltre il notebook: come avviarlo in modo persistente, come configurarlo, come metterlo in sicurezza e come salvarne i dati. Non è materiale necessario per la challenge, ma è il riferimento per chi vuole costruirci sopra qualcosa di reale.

## Avvio con Docker Compose

Per un ambiente stabile conviene descrivere il servizio in un file Compose invece di lanciare il container a mano. In questo modo la configurazione è versionata e l'avvio è ripetibile.

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    restart: unless-stopped
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./qdrant_storage:/qdrant/storage
      - ./qdrant_config.yaml:/qdrant/config/production.yaml
    environment:
      QDRANT__SERVICE__API_KEY: ${QDRANT_API_KEY}
```

Il volume sullo storage garantisce la persistenza dei dati tra i riavvii, mentre il secondo volume monta un file di configurazione personalizzato. La direttiva `restart` fa sì che il container risalga da solo dopo un riavvio della macchina.

## Configurazione

Qdrant si configura tramite un file YAML oppure tramite variabili d'ambiente, dove ogni livello di annidamento è separato da un doppio underscore. Le due modalità sono equivalenti e si possono mescolare, con le variabili d'ambiente che hanno la precedenza.

```yaml
service:
  http_port: 6333
  grpc_port: 6334

storage:
  storage_path: /qdrant/storage
  on_disk_payload: true

log_level: INFO
```

L'opzione `on_disk_payload` tiene il payload su disco invece che in memoria, scelta sensata quando i payload sono grandi e la memoria è una risorsa scarsa. I vettori, al contrario, conviene tenerli in memoria per la velocità, a meno di non usare la quantizzazione.

## Sicurezza

Per impostazione predefinita Qdrant non richiede autenticazione, il che va bene in locale ma è inaccettabile quando il servizio è esposto in rete. La protezione minima è una chiave API, impostata via configurazione o variabile d'ambiente, che va poi fornita a ogni richiesta del client.

```python
from qdrant_client import QdrantClient

client = QdrantClient(
    host="qdrant.miodominio.it",
    port=6333,
    api_key="la-mia-chiave-segreta",
    https=True,
)
```

Oltre alla chiave API conviene terminare il traffico su TLS, così che le richieste viaggino cifrate, e limitare l'accesso alla porta tramite firewall o rete privata. Qdrant supporta anche una chiave di sola lettura, utile per separare i servizi che interrogano l'indice da quelli che lo scrivono.

## Snapshot e backup

Qdrant permette di creare snapshot di una collection, ovvero copie consistenti che possono essere archiviate e ripristinate altrove. È il meccanismo di backup nativo e anche il modo più semplice per migrare una collection da un'istanza all'altra.

```python
# Crea uno snapshot della collection
client.create_snapshot(collection_name="qdrant_docs")

# Elenca gli snapshot disponibili
client.list_snapshots(collection_name="qdrant_docs")
```

Gli snapshot vengono salvati nella cartella di storage del server. In un contesto di produzione vanno poi copiati su uno storage esterno, perché uno snapshot che vive solo sullo stesso disco dei dati non protegge da un guasto di quel disco.

## Qdrant Cloud

Chi non vuole gestire l'infrastruttura può usare Qdrant Cloud, il servizio gestito ufficiale. Si crea un cluster dalla console web, si ottengono un URL e una chiave API, e ci si connette esattamente come a un'istanza self-hosted, cambiando solo i parametri di connessione. Il vantaggio è non doversi occupare di aggiornamenti, scaling e backup, che diventano responsabilità del provider.

```python
client = QdrantClient(
    url="https://xyz-example.eu-central.aws.cloud.qdrant.io:6333",
    api_key="la-chiave-del-cluster-cloud",
)
```

## Dimensionamento

Stimare la memoria necessaria è semplice in prima approssimazione. La componente dominante sono i vettori: il loro peso è il prodotto tra numero di punti, dimensione del vettore e quattro byte per ciascuna componente in virgola mobile a piena precisione. A questo si aggiunge l'overhead dell'indice HNSW, proporzionale al parametro `m`, e l'eventuale payload se tenuto in memoria.

Per un milione di chunk embeddati con `text-embedding-3-small` a `1536` dimensioni, la sola memoria vettoriale supera i sei gigabyte, che scendono sotto i due con la quantizzazione scalare. È spesso la quantizzazione, più che l'aggiunta di hardware, la leva che rende sostenibile una collection di grandi dimensioni.
