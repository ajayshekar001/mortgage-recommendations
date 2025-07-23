from neo4j import GraphDatabase
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_neo4j_connection():
    """Test Neo4j connection and verify it's working properly."""
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "neo4jAjay"
    
    try:
        # Create driver instance
        logger.info("Attempting to connect to Neo4j...")
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # Verify connection
        with driver.session() as session:
            # Run a simple query to verify connection
            result = session.run("RETURN 1 as n")
            record = result.single()
            if record and record["n"] == 1:
                logger.info("Successfully connected to Neo4j!")
                
                # Get server info
                server_info = driver.get_server_info()
                logger.info(f"Neo4j Server Info: {server_info}")
                
                # Get connection pool stats
                pool_stats = driver._pool.stats()
                logger.info(f"Connection Pool Stats: {pool_stats}")
                
                return True
            else:
                logger.error("Connection test failed - query did not return expected result")
                return False
                
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {str(e)}")
        return False
    finally:
        if 'driver' in locals():
            driver.close()
            logger.info("Neo4j connection closed")

if __name__ == "__main__":
    test_neo4j_connection() 