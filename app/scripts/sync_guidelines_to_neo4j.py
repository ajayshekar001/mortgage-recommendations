import json
from pathlib import Path
from app.services.neo4j_knowledge_graph import Neo4jKnowledgeGraph

def sync_guidelines_to_neo4j():
    # Initialize Neo4j service
    kg = Neo4jKnowledgeGraph()

    # Load real guideline data
    guidelines_path = Path("/Users/shekar/blend/hackathon/uploads/selling_guide_chunks_with_openai_embeddings.json")
    with open(guidelines_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    # Add each guideline as a node in Neo4j
    for chunk in chunks:
        # Extract metadata
        metadata = chunk.get('metadata', {})
        section = metadata.get('section', '')
        subsection = metadata.get('subsection', '')
        guideline = {
            "id": chunk.get('id', ''),
            "title": f"{section} - {subsection}" if section and subsection else "Guideline",
            "content": chunk['content'],
            "section": section,
            "subsection": subsection,
            "embedding": chunk.get('embedding', [])
        }
        kg.add_guideline(guideline)

    kg.close()

if __name__ == "__main__":
    sync_guidelines_to_neo4j() 