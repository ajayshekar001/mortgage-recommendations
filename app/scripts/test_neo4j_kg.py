from app.services.neo4j_knowledge_graph import Neo4jKnowledgeGraph

def test_neo4j_kg():
    # Initialize the service
    kg = Neo4jKnowledgeGraph()

    # Add a guideline node
    guideline = {
        "id": 1,
        "title": "Test Guideline",
        "content": "This is a test guideline for Neo4j integration.",
        "section": "A",
        "subsection": "A1"
    }
    kg.add_guideline(guideline)

    # Add another guideline and a relationship
    guideline2 = {
        "id": 2,
        "title": "Second Guideline",
        "content": "Another test guideline.",
        "section": "B",
        "subsection": "B1"
    }
    kg.add_guideline(guideline2)
    kg.add_relationship(1, 2, "prerequisite")

    # Test semantic search
    results = kg.semantic_search("test")
    for node in results:
        print(dict(node))

    kg.close()

if __name__ == "__main__":
    test_neo4j_kg() 