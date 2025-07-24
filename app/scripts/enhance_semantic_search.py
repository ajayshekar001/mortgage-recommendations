from app.services.neo4j_knowledge_graph import Neo4jKnowledgeGraph
import numpy as np
from openai import OpenAI

client = OpenAI(api_key="")

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def enhance_semantic_search():
    kg = Neo4jKnowledgeGraph()

    # Generate query embedding using OpenAI
    query_text = "Your semantic search query here"
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query_text
    )
    query_vector = np.array(response.data[0].embedding)

    # Fetch all guidelines and their embeddings from Neo4j
    with kg.driver.session() as session:
        result = session.run("MATCH (g:Guideline) RETURN g")
        guidelines = [record["g"] for record in result]

    # Calculate similarity scores
    similarities = []
    for guideline in guidelines:
        embedding = np.array(guideline.get('embedding', []))
        if embedding.size > 0:
            similarity = cosine_similarity(query_vector, embedding)
            similarities.append((guideline, similarity))

    # Sort by similarity and get top results
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_results = similarities[:5]  # Get top 5 results

    for guideline, similarity in top_results:
        print(f"Guideline: {dict(guideline)}, Similarity: {similarity}")

    kg.close()

if __name__ == "__main__":
    enhance_semantic_search() 