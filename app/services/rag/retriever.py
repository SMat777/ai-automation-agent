"""RAG retriever — ties chunking, embedding, and vector search together.

The main interface for the RAG pipeline:
- ingest(): text → chunks → embeddings → vector store
- search(): query → embedding → similarity search → ranked results
- format_context(): results → string for LLM context injection
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.rag.chunker import chunk_text
from app.services.rag.embedder import embed_single, embed_texts
from app.services.rag.vectorstore import VectorStore


@dataclass(frozen=True, slots=True)
class SearchResult:
    """A single RAG search result with source citation."""

    text: str
    source: str
    doc_id: str
    score: float  # 0-1, higher is better (1 - cosine distance)
    chunk_id: str


class Retriever:
    """End-to-end RAG retriever for document ingestion and search."""

    def __init__(self, persist_dir: str = "./chroma_data") -> None:
        self._store = VectorStore(persist_dir=persist_dir)

    def ingest(
        self,
        doc_id: str,
        text: str,
        source: str = "",
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> int:
        """Chunk, embed, and store a document.

        Args:
            doc_id: Unique document identifier.
            text: Full document text.
            source: Source filename for citations.
            chunk_size: Max characters per chunk.
            overlap: Overlap between consecutive chunks.

        Returns:
            Number of chunks stored.
        """
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        if not chunks:
            return 0

        texts = [c.text for c in chunks]
        embeddings = embed_texts(texts)
        metadatas = [{"source": source, "chunk_index": c.index} for c in chunks]

        self._store.add(
            doc_id=doc_id,
            texts=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(chunks)

    def search(self, query: str, n_results: int = 5) -> list[SearchResult]:
        """Search the knowledge base for chunks relevant to the query.

        Args:
            query: Natural language search query.
            n_results: Maximum results to return.

        Returns:
            List of SearchResult sorted by relevance (highest score first).
        """
        query_embedding = embed_single(query)
        raw_results = self._store.query(
            embedding=query_embedding, n_results=n_results,
        )

        results: list[SearchResult] = []
        for r in raw_results:
            meta = r.get("metadata", {})
            results.append(SearchResult(
                text=r["text"],
                source=meta.get("source", ""),
                doc_id=meta.get("doc_id", ""),
                score=round(1.0 - r.get("distance", 0.0), 4),
                chunk_id=r.get("id", ""),
            ))

        return results

    def format_context(self, results: list[SearchResult]) -> str:
        """Format search results into a context string for LLM injection.

        Args:
            results: List of search results from search().

        Returns:
            Formatted string with sources and text chunks.
        """
        if not results:
            return "No relevant documents found in knowledge base."

        parts: list[str] = []
        for i, r in enumerate(results, 1):
            source_label = f" (source: {r.source})" if r.source else ""
            parts.append(
                f"[{i}]{source_label} (relevance: {r.score:.0%})\n{r.text}"
            )

        return "Knowledge base context:\n\n" + "\n\n---\n\n".join(parts)

    def delete_document(self, doc_id: str) -> None:
        """Remove a document and all its chunks from the store."""
        self._store.delete(doc_id=doc_id)

    def list_documents(self) -> list[str]:
        """List all document IDs in the knowledge base."""
        return self._store.list_documents()
