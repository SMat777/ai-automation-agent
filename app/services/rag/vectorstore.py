"""ChromaDB vector store for document chunks.

Stores embedded text chunks with metadata and supports
similarity search for RAG retrieval.
"""

from __future__ import annotations

from typing import Any

import chromadb

_COLLECTION_NAME = "knowledge_base"


class VectorStore:
    """Thin wrapper around ChromaDB for document storage and retrieval."""

    def __init__(self, persist_dir: str = "./chroma_data") -> None:
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def add(
        self,
        doc_id: str,
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add document chunks to the store.

        Args:
            doc_id: Unique identifier for the source document.
            texts: List of text chunks.
            embeddings: Corresponding embedding vectors.
            metadatas: Optional per-chunk metadata dicts.
        """
        ids = [f"{doc_id}-{i}" for i in range(len(texts))]
        metas = metadatas or [{} for _ in texts]
        # Ensure every metadata dict carries the doc_id
        for m in metas:
            m["doc_id"] = doc_id

        self._collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metas,
        )

    def query(
        self,
        embedding: list[float],
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Find the most similar chunks to the query embedding.

        Args:
            embedding: Query vector.
            n_results: Number of results to return.
            where: Optional ChromaDB filter dict.

        Returns:
            List of dicts with keys: text, metadata, distance, id.
        """
        kwargs: dict[str, Any] = {
            "query_embeddings": [embedding],
            "n_results": n_results,
        }
        if where:
            kwargs["where"] = where

        raw = self._collection.query(**kwargs)

        results: list[dict[str, Any]] = []
        docs = raw.get("documents", [[]])[0]
        metas = raw.get("metadatas", [[]])[0]
        dists = raw.get("distances", [[]])[0]
        ids = raw.get("ids", [[]])[0]

        for text, meta, dist, chunk_id in zip(docs, metas, dists, ids):
            results.append({
                "text": text,
                "metadata": meta,
                "distance": dist,
                "id": chunk_id,
            })

        return results

    def delete(self, doc_id: str) -> None:
        """Remove all chunks belonging to a document.

        Args:
            doc_id: The document ID whose chunks to delete.
        """
        existing = self._collection.get(where={"doc_id": doc_id})
        chunk_ids = existing.get("ids", [])
        if chunk_ids:
            self._collection.delete(ids=chunk_ids)

    def list_documents(self) -> list[str]:
        """Return unique document IDs stored in the collection."""
        all_data = self._collection.get()
        metas = all_data.get("metadatas", [])
        doc_ids: set[str] = set()
        for meta in metas:
            if isinstance(meta, dict) and "doc_id" in meta:
                doc_ids.add(meta["doc_id"])
        return sorted(doc_ids)

    @property
    def count(self) -> int:
        """Total number of chunks in the store."""
        return self._collection.count()
