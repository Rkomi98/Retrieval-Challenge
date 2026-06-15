# Qdrant e Pinecone a confronto

Qdrant e Pinecone risolvono lo stesso problema — conservare vettori e recuperarli per similarità — ma incarnano due filosofie opposte su chi debba gestire l'infrastruttura. Conoscere le differenze aiuta a scegliere, ma soprattutto chiarisce che i concetti di fondo del retrieval non cambiano da un sistema all'altro.

## Open source contro servizio gestito

Qdrant è open source e scritto in Rust: si può eseguire in locale con Docker, in modalità in-memory dentro un notebook, oppure su una propria macchina in produzione. Il codice è ispezionabile e non c'è dipendenza da un fornitore. Pinecone è un servizio gestito: non si installa e non si vede il codice, si accede solo tramite API. Con Qdrant si ha controllo completo al prezzo dell'onere operativo; con Pinecone si delega tutto al fornitore al prezzo del vincolo a un servizio esterno.

## Terminologia a confronto

I due sistemi usano nomi diversi per concetti molto simili. La tabella seguente mette in corrispondenza i termini che si incontrano più spesso.

| Concetto | Qdrant | Pinecone |
|---|---|---|
| Contenitore dei vettori | collection | index |
| Partizione logica interna | — (si usano i filtri) | namespace |
| Dato non vettoriale allegato | payload | metadata |
| Scrittura idempotente | `upsert` | `upsert` |
| Ricerca per similarità | `query_points` / `search` | `query` |
| Numero di risultati | `limit` | `top_k` |

La simmetria non è casuale: entrambi conservano un vettore, un identificatore e un dizionario di metadati, ed entrambi recuperano i vicini più prossimi secondo una metrica di distanza fissata alla creazione del contenitore.

## Modello di costo

Qdrant, se eseguito in proprio, ha il costo della macchina su cui gira e del tempo per amministrarlo; non c'è un canone per le operazioni. Pinecone in modalità serverless si paga a consumo, in base a letture, scritture e dati conservati: niente costi fissi quando è inattivo, ma una spesa che cresce con l'uso e va monitorata. Esiste anche Qdrant Cloud, che offre Qdrant come servizio gestito e avvicina i due modelli di costo.

## Filtraggio sui metadati

Entrambi supportano il recupero mirato vincolando i metadati. Qdrant lo esprime con un oggetto `Filter` composto da `FieldCondition`; Pinecone con un dizionario in stile MongoDB e operatori come `$eq` e `$in`. In tutti e due i casi il filtro agisce durante la ricerca: i risultati restituiti sono i più vicini tra quelli che rispettano la condizione, non un sottoinsieme filtrato a posteriori.

## Come scegliere

Per un prototipo o per un corso, Qdrant in modalità in-memory è imbattibile: zero installazione, zero costi, tutto dentro il processo Python. Per andare in produzione senza un team che gestisca infrastruttura, Pinecone serverless toglie ogni onere operativo. Tra i due estremi ci sono Qdrant self-hosted e Qdrant Cloud. La decisione raramente dipende dalla qualità del retrieval, che è comparabile, e quasi sempre dal contesto: competenze del team, vincoli di costo, requisiti di controllo sui dati.
