from app.services.neo4j_knowledge_graph import Neo4jKnowledgeGraph

def run_advanced_queries():
    kg = Neo4jKnowledgeGraph()

    # Example 1: Find all prerequisites for a specific guideline
    def find_prerequisites(guideline_id):
        with kg.driver.session() as session:
            result = session.run(
                """
                MATCH (g:Guideline {id: $id})<-[:NEXT]-(prereq:Guideline)
                RETURN prereq
                """,
                id=guideline_id
            )
            return [record["prereq"] for record in result]

    # Example 2: Identify related guidelines based on content similarity
    def find_related_guidelines(guideline_id):
        with kg.driver.session() as session:
            result = session.run(
                """
                MATCH (g:Guideline {id: $id})-[:RELATED]->(related:Guideline)
                RETURN related
                """,
                id=guideline_id
            )
            return [record["related"] for record in result]

    # Example 3: Traverse the graph to find paths between guidelines
    def find_paths_between_guidelines(start_id, end_id):
        with kg.driver.session() as session:
            result = session.run(
                """
                MATCH path = (start:Guideline {id: $start_id})-[*]-(end:Guideline {id: $end_id})
                RETURN path
                """,
                start_id=start_id,
                end_id=end_id
            )
            return [record["path"] for record in result]

    # Example usage
    guideline_id = "example_id"  # Replace with an actual guideline ID
    print("Prerequisites:", find_prerequisites(guideline_id))
    print("Related Guidelines:", find_related_guidelines(guideline_id))
    print("Paths between guidelines:", find_paths_between_guidelines("start_id", "end_id"))

    kg.close()

if __name__ == "__main__":
    run_advanced_queries() 