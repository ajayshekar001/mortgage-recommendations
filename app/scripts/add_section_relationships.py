from collections import defaultdict
from app.services.neo4j_knowledge_graph import Neo4jKnowledgeGraph
import json
from pathlib import Path

def add_section_relationships():
    kg = Neo4jKnowledgeGraph()
    guidelines_path = Path("/Users/shekar/blend/hackathon/uploads/selling_guide_chunks_with_openai_embeddings.json")
    with open(guidelines_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    # Group by section
    section_map = defaultdict(list)
    for chunk in chunks:
        section = chunk.get('metadata', {}).get('section', '')
        if section:
            section_map[section].append(chunk.get('id', ''))

    # Add SAME_SECTION relationships
    for ids in section_map.values():
        for i in range(len(ids)):
            for j in range(i+1, len(ids)):
                kg.add_relationship(ids[i], ids[j], "SAME_SECTION")
    kg.close()

if __name__ == "__main__":
    add_section_relationships() 