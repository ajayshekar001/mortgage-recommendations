from app.services.neo4j_knowledge_graph import Neo4jKnowledgeGraph
import json
from pathlib import Path

def add_sequential_relationships():
    kg = Neo4jKnowledgeGraph()
    guidelines_path = Path("/Users/shekar/blend/hackathon/uploads/selling_guide_chunks_with_openai_embeddings.json")
    with open(guidelines_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    # Sort by id or any order you want
    chunks = sorted(chunks, key=lambda x: x.get('id', ''))
    for i in range(len(chunks) - 1):
        source_id = chunks[i].get('id', '')
        target_id = chunks[i+1].get('id', '')
        if source_id and target_id:
            kg.add_relationship(source_id, target_id, "NEXT")
    kg.close()

if __name__ == "__main__":
    add_sequential_relationships() 