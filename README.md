# Capstone S07 — Retrieval Challenge

> Consolidamento di **ingestion** e **retrieval** su un corpus reale. ~40 minuti.
> Niente generation: ci fermiamo al recupero dei chunk giusti.

## Lo scenario

Sei un/una AI engineer e ti viene dato un piccolo corpus di documentazione in
italiano su **database vettoriali** (Qdrant e Pinecone). Devi costruire la
pipeline che, data una domanda tecnica, recupera i pezzi di documentazione che
contengono la risposta.

Hai già lo scheletro del progetto e un **giudice automatico** (`evaluate.py`)
che misura quanto bene recuperi: ti dice, su un insieme di domande, in quante
hai trovato la fonte giusta. Il tuo lavoro è **completare la pipeline** e poi
**far salire quel punteggio** scegliendo bene i parametri.

## Come si vince

Il punteggio è **`hit@k`**: su `N` domande del gold set, in quante almeno uno dei
primi `k` chunk recuperati viene dal file giusto. Il giudice lo riporta a tre
profondità:

```
  hit@1 =  9/14  ( 64%)  <- punteggio principale (ranking)
  hit@2 = 13/14  ( 93%)
  hit@3 = 14/14  (100%)
```

**`hit@1` è la misura che conta**: vuol dire che il chunk giusto è arrivato
*primo*, cioè che il retrieval ha davvero capito la domanda. `hit@2` e `hit@3`
sono più indulgenti (basta che la fonte sia "lì intorno"). Far salire `hit@1`
è la sfida.

> Nota: è una verifica volutamente semplice. La teoria della valutazione del
> retrieval (recall, precision, MRR…) arriva in una lezione dedicata — qui ci
> serve solo un numero che salga quando le tue scelte migliorano.

## Le regole d'ordine (importanti quanto il punteggio)

Questo progetto è strutturato come un progetto vero, e va tenuto tale:

- **Tutti i parametri stanno in `config.py`.** Niente numeri magici sparsi nel
  codice: chunk size, modello, top_k si cambiano lì e basta.
- **I segreti stanno nel `.env`**, mai nel codice. Versioni solo `.env.example`.
- **Ingestion, retrieval e valutazione vivono in file separati.** Ognuno fa una
  cosa.
- **I dati stanno in `data/`**, fuori dal codice.

Lavora *dentro* questa struttura: è metà del valore dell'esercizio.

## Cosa devi completare

Tre `# TODO`, tutti su cose già viste a lezione:

| File | TODO | Cosa |
|------|------|------|
| `src/ingest.py` | TODO 1 | Embeddare i chunk |
| `src/ingest.py` | TODO 2 | Caricarli su Qdrant (`store.add`) |
| `src/retrieve.py` | TODO | Embeddare la query e cercare i `k` vicini |

Quando i tre TODO sono fatti, `python scripts/evaluate.py` produce un punteggio.

## Le tre leve da tunare (per far salire il punteggio)

Tutte in `config.py`:

1. **`EMBEDDER`** — quale modello di embedding. Provane diversi:
   - `openai` → `text-embedding-3-small` (serve la chiave)
   - `minilm-it`, `e5-small`, `bge-m3` → **locali e gratuiti**, multilingue
   - `minilm-en` → **locale e gratuito ma solo inglese**. Il corpus è in
     italiano: provalo e guarda `hit@1` crollare. È l'esperimento più istruttivo
     della challenge — la scelta del modello *giusto per la lingua* conta più
     del modello "più famoso".
2. **Chunking** — `CHUNK_MAX_CHAR`, `CHUNK_OVERLAP`, `STRUCTURE_AWARE`.
   Chunk troppo grandi diluiscono il significato, troppo piccoli lo spezzano.
   `STRUCTURE_AWARE=True` evita di tagliare i blocchi di codice a metà.
3. **`TOP_K`** — quanti chunk recuperi. Più alto = più facile beccare la fonte,
   ma in una RAG vera significa più rumore passato al modello. Qual è il
   compromesso?

> ⚠️ Inghippo utile: ogni modello ha una **dimensione vettoriale diversa**. Lo
> starter ricrea la collection con la dimensione giusta leggendo `embedder.dim`,
> quindi puoi cambiare modello senza pensarci — ma ricordati *perché* serve.

## Come partire

```bash
# 1. attiva il venv del corso (stesso di Lez07) — o installa da requirements.txt
# 2. completa i TODO, poi lancia il giudice
python scripts/evaluate.py
```

Il default è `EMBEDDER = "minilm-it"`: parte **senza chiave** (modello locale,
si scarica la prima volta). Se vuoi provare `openai`, copia `.env.example` in
`.env` e metti la chiave.

## Struttura del progetto

```
S07_Capstone_Retrieval/
├── README.md            # questa consegna
├── config.py            # TUTTI i parametri (le 3 leve)
├── .env.example         # template dei segreti
├── requirements.txt
├── data/
│   ├── corpus/          # 8 documenti .md (Qdrant + Pinecone)
│   └── gold/queries.json# le domande con la fonte attesa
├── src/
│   ├── embeddings.py    # factory: cambi modello con una stringa
│   ├── ingest.py        # load → chunk → embed → upsert   (2 TODO)
│   └── retrieve.py      # query → search → top_k          (1 TODO)
└── scripts/
    └── evaluate.py      # il giudice (hit@k) — NON si tocca
```

## Sfide bonus (per chi finisce prima)

- **Retrieval filtrato**: implementa `retrieve_filtered` in `src/retrieve.py` per
  cercare solo dentro un file specifico (filtro sui metadati).
- **Caccia all'errore**: trova una domanda del gold set che sbagli sempre. È
  colpa del chunking, dell'embedding o di com'è scritta la domanda?
- **La tua domanda**: aggiungi una riga al gold set e verifica che la pipeline
  la gestisca.
