from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.knowledge_graph import Guideline
from app.db.session import SessionLocal
from openai import OpenAI
from app.core.config import settings
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

class KnowledgeGraphService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.db = SessionLocal()

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for a given text using OpenAI's API."""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def add_guideline(self, title: str, content: str, section: str, subsection: str) -> Guideline:
        """Add a new guideline to the knowledge graph."""
        # Generate embedding for the guideline
        embedding = self._get_embedding(f"{title} {content}")
        
        # Create new guideline
        guideline = Guideline(
            title=title,
            content=content,
            section=section,
            subsection=subsection
        )
        guideline.set_embedding_vector(embedding)
        
        self.db.add(guideline)
        self.db.commit()
        self.db.refresh(guideline)
        
        return guideline

    def add_relationship(self, source_id: int, target_id: int, relationship_type: str) -> None:
        """Add a relationship between two guidelines."""
        source = self.db.query(Guideline).get(source_id)
        target = self.db.query(Guideline).get(target_id)
        
        if relationship_type == 'prerequisite':
            source.prerequisites.append(target)
        elif relationship_type == 'exception':
            source.exceptions.append(target)
        elif relationship_type == 'related':
            source.related_guidelines.append(target)
        
        self.db.commit()

    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search on the knowledge graph."""
        # Get embedding for the query
        query_embedding = self._get_embedding(query)
        
        # Get all guidelines
        guidelines = self.db.query(Guideline).all()
        
        # Calculate similarities
        similarities = []
        for guideline in guidelines:
            guideline_embedding = guideline.get_embedding_vector()
            if not guideline_embedding:
                continue
                
            similarity = cosine_similarity(
                [query_embedding],
                [guideline_embedding]
            )[0][0]
            
            similarities.append((guideline, similarity))
        
        # Sort by similarity and get top_k results
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_results = similarities[:top_k]
        
        # Format results with context from the knowledge graph
        results = []
        for guideline, score in top_results:
            result = {
                "guideline": guideline.to_dict(),
                "similarity_score": float(score),
                "context": {
                    "prerequisites": [p.to_dict() for p in guideline.prerequisites],
                    "exceptions": [e.to_dict() for e in guideline.exceptions],
                    "related_guidelines": [r.to_dict() for r in guideline.related_guidelines]
                }
            }
            results.append(result)
        
        return results

    def search_with_context(self, query: str, context: str = "", top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search with additional context."""
        full_query = f"{context} {query}" if context else query
        return self.semantic_search(full_query, top_k)

    def get_guideline_path(self, guideline_id: int) -> Dict[str, Any]:
        """Get the full path of prerequisites for a guideline."""
        guideline = self.db.query(Guideline).get(guideline_id)
        if not guideline:
            return {}
        
        path = {
            "current": guideline.to_dict(),
            "prerequisites": [],
            "exceptions": [],
            "related": []
        }
        
        # Get all prerequisites recursively
        for prereq in guideline.prerequisites:
            path["prerequisites"].append(self.get_guideline_path(prereq.id))
        
        # Get all exceptions
        for exception in guideline.exceptions:
            path["exceptions"].append(exception.to_dict())
        
        # Get all related guidelines
        for related in guideline.related_guidelines:
            path["related"].append(related.to_dict())
        
        return path

    def __del__(self):
        """Clean up database session."""
        self.db.close() 