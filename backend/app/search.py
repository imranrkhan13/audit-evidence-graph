"""Deterministic evidence retrieval — a from-scratch TF-IDF vector search.

This is the "vector store" layer: every document page is a vector in
term-frequency/inverse-document-frequency space, and a query is scored
against every page by cosine similarity. It is a real, working
implementation of the concept a production system would back with an
embeddings API — swapping in real embeddings later would only mean
replacing `_vectorize()` below, since everything downstream just consumes
a {page_id: score} ranking.

CRITICAL BOUNDARY: this module's only job is to help a human *find*
evidence faster. It has no opinion on whether a number ties out. Nothing
in app/tie_out.py or app/engine.py calls into this file, and nothing here
writes to Assertion.status. That separation is deliberate and is covered
by test_search.py.
"""
import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import List

TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> List[str]:
    return TOKEN_RE.findall(text.lower())


@dataclass
class SearchResult:
    document_id: str
    document_title: str
    page_number: int
    score: float
    snippet: str


def search_pages(pages: list, query: str, top_k: int = 10) -> List[SearchResult]:
    """pages: list of dicts with document_id, document_title, page_number, text_content."""
    if not query.strip() or not pages:
        return []

    corpus_tokens = [_tokenize(p["text_content"]) for p in pages]
    n_docs = len(corpus_tokens)

    df = Counter()
    for tokens in corpus_tokens:
        for term in set(tokens):
            df[term] += 1
    idf = {term: math.log((1 + n_docs) / (1 + count)) + 1 for term, count in df.items()}

    def vectorize(tokens: List[str]) -> dict:
        tf = Counter(tokens)
        total = len(tokens) or 1
        return {term: (count / total) * idf.get(term, 0.0) for term, count in tf.items()}

    doc_vectors = [vectorize(tokens) for tokens in corpus_tokens]
    query_vector = vectorize(_tokenize(query))

    def cosine(a: dict, b: dict) -> float:
        common = set(a) & set(b)
        dot = sum(a[t] * b[t] for t in common)
        norm_a = math.sqrt(sum(v * v for v in a.values())) or 1e-9
        norm_b = math.sqrt(sum(v * v for v in b.values())) or 1e-9
        return dot / (norm_a * norm_b)

    scored = []
    for page, vec in zip(pages, doc_vectors):
        score = cosine(query_vector, vec)
        if score > 0:
            snippet = page["text_content"].strip().replace("\n", " ")[:180]
            scored.append(SearchResult(
                document_id=page["document_id"], document_title=page["document_title"],
                page_number=page["page_number"], score=round(score, 4), snippet=snippet,
            ))

    scored.sort(key=lambda r: r.score, reverse=True)
    return scored[:top_k]
