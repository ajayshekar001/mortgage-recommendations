import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI
from app.core.config import settings

class SemanticSearchService:
    def __init__(self, embeddings_path: str = "/Users/shekar/blend/hackathon/uploads/selling_guide_chunks_with_openai_embeddings.json"):
        self.embeddings_path = Path(embeddings_path)
        self.chunks = self._load_chunks()
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def _load_chunks(self) -> List[Dict[str, Any]]:
        """Load the chunks with their embeddings from the JSON file."""
        with open(self.embeddings_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for a given text using OpenAI's API."""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search on the chunks using the query.
        
        Args:
            query: The search query
            top_k: Number of most relevant results to return
            
        Returns:
            List of dictionaries containing the most relevant chunks with their similarity scores
        """
        # Get embedding for the query
        query_embedding = self._get_embedding(query)
        
        # Calculate similarity scores for all chunks
        similarities = []
        for chunk in self.chunks:
            if "embedding" not in chunk:
                continue
            similarity = self._cosine_similarity(query_embedding, chunk["embedding"])
            similarities.append((chunk, similarity))
        
        # Sort by similarity score and get top_k results
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_results = similarities[:top_k]
        
        # Format results
        results = []
        for chunk, score in top_results:
            result = {
                "content": chunk["content"],
                "similarity_score": float(score),
                "metadata": chunk.get("metadata", {}),
                "id": chunk.get("id")
            }
            results.append(result)
        
        return results

    def search_with_context(self, query: str, context: str = "", top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search with additional context.
        
        Args:
            query: The search query
            context: Additional context to consider in the search
            top_k: Number of most relevant results to return
            
        Returns:
            List of dictionaries containing the most relevant chunks with their similarity scores
        """
        # Combine query and context
        full_query = f"{context} {query}" if context else query
        return self.search(full_query, top_k) 