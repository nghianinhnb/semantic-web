#!/usr/bin/env python3
import os
from typing import List, Tuple

import faiss
import numpy as np
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer


FUSEKI_URL = os.environ.get("FUSEKI_URL", "http://localhost:3030/vn")
QUERY_URL = f"{FUSEKI_URL}/query"


class QueryRequest(BaseModel):
    question: str


def query_triples_for_context() -> List[str]:
    sparql = """
    PREFIX ex: <http://example.org/vn/ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?s ?p ?o WHERE {
      ?s ?p ?o .
      FILTER(?p IN (ex:formedBy, ex:mergedInto, rdfs:label, ex:canonicalLabel))
    }
    LIMIT 5000
    """
    r = requests.get(QUERY_URL, params={"query": sparql, "format": "application/sparql-results+json"}, timeout=30)
    r.raise_for_status()
    data = r.json()["results"]["bindings"]
    docs: List[str] = []
    for b in data:
        s = b["s"]["value"]
        p = b["p"]["value"].split("#")[-1]
        o = b["o"]["value"]
        docs.append(f"{s} {p} {o}")
    return docs


class RAGIndex:
    def __init__(self) -> None:
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = None
        self.corpus: List[str] = []

    def build(self) -> None:
        self.corpus = query_triples_for_context()
        if not self.corpus:
            self.index = None
            return
        emb = self.model.encode(self.corpus, convert_to_numpy=True, show_progress_bar=False)
        d = emb.shape[1]
        self.index = faiss.IndexFlatIP(d)
        faiss.normalize_L2(emb)
        self.index.add(emb)

    def search(self, query: str, k: int = 5) -> List[Tuple[str, float]]:
        if not self.index:
            return []
        q = self.model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(q)
        scores, idx = self.index.search(q, k)
        results: List[Tuple[str, float]] = []
        for i, s in zip(idx[0], scores[0]):
            if i >= 0 and i < len(self.corpus):
                results.append((self.corpus[i], float(s)))
        return results


app = FastAPI()
rag_index = RAGIndex()


@app.on_event("startup")
def startup_event() -> None:
    rag_index.build()


@app.post("/ask")
def ask(req: QueryRequest):
    hits = rag_index.search(req.question, k=8)
    return {"question": req.question, "context": hits}


