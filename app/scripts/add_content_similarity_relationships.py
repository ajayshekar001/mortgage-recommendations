from app.services.neo4j_knowledge_graph import Neo4jKnowledgeGraph
import json
from pathlib import Path
from collections import Counter

def add_content_similarity_relationships(threshold=0.1):
    kg = Neo4jKnowledgeGraph()
    guidelines_path = Path("/Users/shekar/blend/hackathon/uploads/selling_guide_chunks_with_openai_embeddings.json")
    with open(guidelines_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    # Process each chunk to extract keywords (simple word-based approach)
    for i, chunk1 in enumerate(chunks):
        content1 = chunk1.get('content', '').lower()
        words1 = set(content1.split())
        for j, chunk2 in enumerate(chunks[i+1:], i+1):
            content2 = chunk2.get('content', '').lower()
            words2 = set(content2.split())
            # Calculate overlap
            overlap = len(words1.intersection(words2)) / max(len(words1), len(words2))
            if overlap > threshold:
                source_id = chunk1.get('id', '')
                target_id = chunk2.get('id', '')
                if source_id and target_id:
                    kg.add_relationship(source_id, target_id, "RELATED")
    kg.close()

if __name__ == "__main__":
    add_content_similarity_relationships() 