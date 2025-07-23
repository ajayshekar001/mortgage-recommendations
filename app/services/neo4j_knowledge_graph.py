from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import numpy as np
from openai import OpenAI
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Neo4jKnowledgeGraph:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="neo4jAjay"):
        """Initialize Neo4j connection with connection pooling configuration."""
        try:
            self.driver = GraphDatabase.driver(
                uri,
                auth=(user, password),
                max_connection_lifetime=3600,  # 1 hour
                max_connection_pool_size=50,
                connection_timeout=30
            )
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            logger.info("Neo4j connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j connection: {str(e)}")
            raise

    def close(self):
        """Close the Neo4j connection properly."""
        try:
            if hasattr(self, 'driver'):
                self.driver.close()
                logger.info("Neo4j connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing Neo4j connection: {str(e)}")

    def __enter__(self):
        """Support for context manager protocol."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure connection is closed when using context manager."""
        self.close()

    def verify_connection(self) -> bool:
        """Verify that the connection is working."""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as n")
                return result.single()["n"] == 1
        except Exception as e:
            logger.error(f"Connection verification failed: {str(e)}")
            return False

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI API"""
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def add_guideline(self, guideline):
        with self.driver.session() as session:
            session.run(
                """
                MERGE (g:Guideline {id: $id})
                SET g.title = $title, g.content = $content, g.section = $section, g.subsection = $subsection, g.embedding = $embedding
                """,
                id=guideline["id"],
                title=guideline["title"],
                content=guideline["content"],
                section=guideline["section"],
                subsection=guideline["subsection"],
                embedding=guideline.get("embedding", [])
            )

    def add_relationship(self, source_id, target_id, rel_type):
        with self.driver.session() as session:
            session.run(
                f"""
                MATCH (a:Guideline {{id: $source_id}}), (b:Guideline {{id: $target_id}})
                MERGE (a)-[r:{rel_type.upper()}]->(b)
                """,
                source_id=source_id,
                target_id=target_id
            )

    def semantic_search(self, query: str, limit: int = 5, include_metadata: bool = True) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings with enhanced metadata"""
        query_embedding = self._get_embedding(query)
        
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (g:Guideline)
                WITH g, g.embedding AS embedding
                WHERE embedding IS NOT NULL
                WITH g, embedding, 
                     reduce(acc = 0.0, i IN range(0, size(embedding)-1) | 
                           acc + embedding[i] * $query_embedding[i]) / 
                     (sqrt(reduce(acc = 0.0, x IN embedding | acc + x * x)) * 
                      sqrt(reduce(acc = 0.0, x IN $query_embedding | acc + x * x))) 
                AS similarity
                ORDER BY similarity DESC
                RETURN g, similarity
                LIMIT $limit
                """,
                query_embedding=query_embedding,
                limit=limit
            )
            
            # Process results and exclude embeddings while keeping essential context
            processed_results = []
            for record in result:
                guideline_data = dict(record["g"])
                
                # Remove embedding to reduce response size
                if "embedding" in guideline_data:
                    del guideline_data["embedding"]
                
                # Keep essential fields that help the LLM
                processed_guideline = {
                    "id": guideline_data.get("id"),
                    "title": guideline_data.get("title"),
                    "content": guideline_data.get("content"),
                    "section": guideline_data.get("section"),
                    "subsection": guideline_data.get("subsection"),
                    "category": guideline_data.get("category"),
                    "source": guideline_data.get("source"),
                    "version": guideline_data.get("version"),
                    "last_updated": guideline_data.get("last_updated"),
                    "priority": guideline_data.get("priority"),
                    "applicability": guideline_data.get("applicability")
                }
                
                # Remove None values
                processed_guideline = {k: v for k, v in processed_guideline.items() if v is not None}
                
                result_item = {
                    "guideline": processed_guideline,
                    "similarity": record["similarity"],
                    "metadata": {
                        "category": guideline_data.get("category", "Unknown"),
                        "source": guideline_data.get("source", "Unknown"),
                        "section": guideline_data.get("section", "Unknown")
                    } if include_metadata else {}
                }
                
                processed_results.append(result_item)
            
            return processed_results

    def multi_hop_search(self, query: str, max_hops: int = 3, limit: int = 5, include_relationships: bool = True) -> List[Dict[str, Any]]:
        """
        Enhanced multi-hop search using multiple strategies:
        1. Semantic similarity search for starting nodes
        2. Query decomposition for complex queries
        3. Fallback to related guidelines when direct matches fail
        4. Breadth-first path exploration
        5. Enhanced relationship detection and path quality scoring
        6. Dynamic hop limits based on query complexity
        """
        with self.driver.session() as session:
            results = []
            
            # Query Intent Recognition and Dynamic Hop Limits
            query_intent = self._analyze_query_intent(query)
            dynamic_max_hops = self._calculate_dynamic_hops(query, query_intent, max_hops)
            logger.info(f"Query intent: {query_intent['type']}, Dynamic max_hops: {dynamic_max_hops}")
            
            # Strategy 1: Semantic similarity search for starting nodes
            logger.info(f"Strategy 1: Semantic similarity search for query: {query}")
            start_nodes = self._get_semantic_start_nodes(query, session, limit=10)
            
            if start_nodes:
                logger.info(f"Found {len(start_nodes)} starting nodes via semantic search")
                results.extend(self._explore_paths_from_nodes(start_nodes, dynamic_max_hops, limit, session, include_relationships))
            
            # Strategy 2: Query decomposition for complex queries
            if len(results) < limit and len(query.split()) > 3:
                logger.info(f"Strategy 2: Query decomposition for complex query")
                decomposed_results = self._decompose_and_search(query, dynamic_max_hops, limit - len(results), session, include_relationships)
                results.extend(decomposed_results)
            
            # Strategy 3: Fallback to related guidelines
            if len(results) < limit:
                logger.info(f"Strategy 3: Fallback to related guidelines")
                fallback_results = self._fallback_search(query, dynamic_max_hops, limit - len(results), session, include_relationships)
                results.extend(fallback_results)
            
            # Strategy 4: Find highly connected guidelines as starting points
            if len(results) < limit:
                logger.info(f"Strategy 4: Highly connected guidelines search")
                connected_results = self._connected_guidelines_search(query, dynamic_max_hops, limit - len(results), session, include_relationships)
                results.extend(connected_results)
            
            # Enhanced relationship detection and path quality scoring
            enhanced_results = self._enhance_paths_with_relationships(results, session)
            scored_results = self._score_path_quality(enhanced_results, query_intent)
            
            # Remove duplicates and limit results
            unique_results = self._deduplicate_results(scored_results)
            final_results = unique_results[:limit]
            
            # Generate comprehensive path analysis
            path_analysis = self._generate_path_analysis(final_results)
            
            logger.info(f"Multi-hop search completed: {len(final_results)} unique paths found with quality scores")
            
            return {
                "paths": final_results,
                "path_analysis": path_analysis,
                "search_metadata": {
                    "query": query,
                    "max_hops": dynamic_max_hops,
                    "original_max_hops": max_hops,
                    "total_paths_found": len(final_results),
                    "search_strategies_used": self._get_used_strategies(results, limit),
                    "query_intent": query_intent,
                    "path_quality_stats": self._get_path_quality_stats(final_results)
                }
            }

    def _get_semantic_start_nodes(self, query: str, session, limit: int = 10) -> List[Dict]:
        """Get starting nodes using semantic similarity"""
        query_embedding = self._get_embedding(query)
        
        result = session.run(
            """
            MATCH (g:Guideline)
            WITH g, g.embedding AS embedding
            WHERE embedding IS NOT NULL
            WITH g, embedding, 
                 reduce(acc = 0.0, i IN range(0, size(embedding)-1) | 
                       acc + embedding[i] * $query_embedding[i]) / 
                 (sqrt(reduce(acc = 0.0, x IN embedding | acc + x * x)) * 
                  sqrt(reduce(acc = 0.0, x IN $query_embedding | acc + x * x))) 
            AS similarity
            WHERE similarity > 0.3  // Minimum similarity threshold
            ORDER BY similarity DESC
            RETURN g, similarity
            LIMIT $limit
            """,
            query_embedding=query_embedding,
            limit=limit
        )
        
        return [{"node": dict(record["g"]), "similarity": record["similarity"]} for record in result]

    def _explore_paths_from_nodes(self, start_nodes: List[Dict], max_hops: int, limit: int, session, include_relationships: bool) -> List[Dict]:
        """Explore paths from given starting nodes"""
        results = []
        
        for start_node_info in start_nodes:
            start_node = start_node_info["node"]
            
            # Find paths up to max_hops
            cypher = f"""
            MATCH path = (start:Guideline)-[*1..{max_hops}]-(related:Guideline)
            WHERE start.id = $start_id AND related.id <> start.id
            WITH path, [node IN nodes(path) | node] as nodes_in_path, 
                 [rel IN relationships(path) | rel] as relationships_in_path,
                 length(path) as hop_count
            RETURN nodes_in_path, relationships_in_path, hop_count
            LIMIT $limit
            """
            
            path_results = session.run(
                cypher,
                start_id=start_node['id'],
                limit=limit
            ).data()
            
            for path_result in path_results:
                processed_nodes = self._process_nodes(path_result["nodes_in_path"])
                
                result_item = {
                    "path": processed_nodes,
                    "hop_count": path_result["hop_count"],
                    "start_similarity": start_node_info["similarity"]
                }
                
                if include_relationships:
                    result_item["relationships"] = [{"type": rel.type} for rel in path_result["relationships_in_path"] if hasattr(rel, 'type')]
                
                results.append(result_item)
                
                if len(results) >= limit:
                    break
            
            if len(results) >= limit:
                break
        
        return results

    def _decompose_and_search(self, query: str, max_hops: int, limit: int, session, include_relationships: bool) -> List[Dict]:
        """Decompose complex query into components and search each"""
        # Extract key terms from query
        key_terms = self._extract_key_terms(query)
        results = []
        
        for term in key_terms[:3]:  # Limit to top 3 terms
            if len(results) >= limit:
                break
                
            # Search for guidelines containing this term
            term_nodes = session.run(
                """
                MATCH (g:Guideline)
                WHERE g.content CONTAINS $term OR g.title CONTAINS $term
                RETURN g
                LIMIT 3
                """,
                term=term
            ).data()
            
            if term_nodes:
                start_nodes = [{"node": dict(node['g']), "similarity": 0.5} for node in term_nodes]
                term_results = self._explore_paths_from_nodes(start_nodes, max_hops, limit - len(results), session, include_relationships)
                results.extend(term_results)
        
        return results

    def _extract_key_terms(self, query: str) -> List[str]:
        """Extract key terms from query for decomposition"""
        # Simple term extraction - could be enhanced with NLP
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'how', 'what', 'when', 'where', 'why'}
        terms = query.lower().split()
        key_terms = [term for term in terms if term not in stop_words and len(term) > 3]
        return key_terms

    def _fallback_search(self, query: str, max_hops: int, limit: int, session, include_relationships: bool) -> List[Dict]:
        """Fallback search using broader criteria"""
        # Find guidelines that might be related to the query topic
        related_nodes = session.run(
            """
            MATCH (g:Guideline)
            WHERE g.content CONTAINS 'credit' OR g.content CONTAINS 'income' OR g.content CONTAINS 'loan' 
               OR g.content CONTAINS 'approval' OR g.content CONTAINS 'documentation'
            RETURN g
            LIMIT 5
            """,
        ).data()
        
        if related_nodes:
            start_nodes = [{"node": dict(node['g']), "similarity": 0.3} for node in related_nodes]
            return self._explore_paths_from_nodes(start_nodes, max_hops, limit, session, include_relationships)
        
        return []

    def _connected_guidelines_search(self, query: str, max_hops: int, limit: int, session, include_relationships: bool) -> List[Dict]:
        """Search starting from highly connected guidelines"""
        # Find guidelines with many relationships
        connected_nodes = session.run(
            """
            MATCH (g:Guideline)-[r]-()
            WITH g, count(r) as connection_count
            ORDER BY connection_count DESC
            LIMIT 5
            RETURN g, connection_count
            """,
        ).data()
        
        if connected_nodes:
            start_nodes = [{"node": dict(node['g']), "similarity": 0.2} for node in connected_nodes]
            return self._explore_paths_from_nodes(start_nodes, max_hops, limit, session, include_relationships)
        
        return []

    def _process_nodes(self, nodes_in_path) -> List[Dict]:
        """Process nodes to exclude embeddings while keeping essential context"""
        processed_nodes = []
        for node in nodes_in_path:
            node_data = dict(node)
            
            # Remove embedding to reduce response size
            if "embedding" in node_data:
                del node_data["embedding"]
            
            # Keep essential fields that help the LLM
            processed_node = {
                "id": node_data.get("id"),
                "title": node_data.get("title"),
                "content": node_data.get("content"),
                "section": node_data.get("section"),
                "subsection": node_data.get("subsection"),
                "category": node_data.get("category"),
                "source": node_data.get("source"),
                "version": node_data.get("version"),
                "last_updated": node_data.get("last_updated"),
                "priority": node_data.get("priority"),
                "applicability": node_data.get("applicability")
            }
            
            # Remove None values
            processed_node = {k: v for k, v in processed_node.items() if v is not None}
            processed_nodes.append(processed_node)
        
        return processed_nodes

    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate paths based on node IDs"""
        seen_paths = set()
        unique_results = []
        
        for result in results:
            path_ids = tuple(sorted([node.get('id', '') for node in result.get('path', [])]))
            if path_ids not in seen_paths and len(path_ids) > 1:  # Ensure at least 2 nodes
                seen_paths.add(path_ids)
                unique_results.append(result)
        
        return unique_results

    def _generate_path_analysis(self, paths: List[Dict]) -> Dict:
        """Generate comprehensive path analysis with examples and insights"""
        if not paths:
            return {
                "summary": "No paths found",
                "path_examples": [],
                "relationship_analysis": {},
                "path_statistics": {}
            }
        
        # Generate path examples
        path_examples = []
        for i, path_result in enumerate(paths[:10]):  # Limit to top 10 examples
            path = path_result.get('path', [])
            hop_count = path_result.get('hop_count', 0)
            
            if len(path) >= 2:
                # Create readable path example
                path_titles = [node.get('title', 'Unknown') or 'Guideline' for node in path]
                path_example = " → ".join(path_titles)
                path_examples.append({
                    "example": path_example,
                    "hop_count": hop_count,
                    "path_id": i + 1,
                    "start_similarity": path_result.get('start_similarity', 0)
                })
        
        # Analyze relationships
        relationship_types = set()
        for path_result in paths:
            relationships = path_result.get('relationships', [])
            for rel in relationships:
                if isinstance(rel, dict) and 'type' in rel:
                    relationship_types.add(rel['type'])
        
        # Path statistics
        hop_counts = [p.get('hop_count', 0) for p in paths]
        similarities = [p.get('start_similarity', 0) for p in paths if p.get('start_similarity')]
        
        path_statistics = {
            "total_paths": len(paths),
            "shortest_paths": len([h for h in hop_counts if h <= 2]),
            "longest_paths": len([h for h in hop_counts if h >= 3]),
            "avg_hop_count": sum(hop_counts) / len(hop_counts) if hop_counts else 0,
            "avg_similarity": sum(similarities) / len(similarities) if similarities else 0,
            "path_complexity": f"Paths range from {min(hop_counts)} to {max(hop_counts)} hops" if hop_counts else "No paths"
        }
        
        # Identify key starting points
        starting_nodes = {}
        for path_result in paths:
            path = path_result.get('path', [])
            if path:
                start_node = path[0]
                start_id = start_node.get('id', 'unknown')
                start_title = start_node.get('title', 'Unknown') or 'Guideline'
                
                if start_id not in starting_nodes:
                    starting_nodes[start_id] = {
                        "title": start_title,
                        "count": 0,
                        "avg_similarity": 0,
                        "similarities": []
                    }
                
                starting_nodes[start_id]["count"] += 1
                if path_result.get('start_similarity'):
                    starting_nodes[start_id]["similarities"].append(path_result['start_similarity'])
        
        # Calculate average similarities for starting nodes
        for node_id, node_data in starting_nodes.items():
            if node_data["similarities"]:
                node_data["avg_similarity"] = sum(node_data["similarities"]) / len(node_data["similarities"])
            del node_data["similarities"]  # Clean up
        
        # Sort starting nodes by count
        sorted_starting_nodes = sorted(starting_nodes.items(), key=lambda x: x[1]["count"], reverse=True)
        
        return {
            "summary": f"Found {len(paths)} unique paths with {len(relationship_types)} relationship types",
            "path_examples": path_examples,
            "relationship_analysis": {
                "relationship_types": list(relationship_types),
                "total_relationships": sum(len(p.get('relationships', [])) for p in paths),
                "avg_relationships_per_path": sum(len(p.get('relationships', [])) for p in paths) / len(paths) if paths else 0
            },
            "path_statistics": path_statistics,
            "starting_nodes": dict(sorted_starting_nodes[:5]),  # Top 5 starting nodes
            "path_insights": self._generate_path_insights(paths)
        }

    def _generate_path_insights(self, paths: List[Dict]) -> List[str]:
        """Generate insights about the discovered paths"""
        insights = []
        
        if not paths:
            return ["No paths found - consider broadening the search or using different keywords"]
        
        # Analyze path lengths
        hop_counts = [p.get('hop_count', 0) for p in paths]
        if hop_counts:
            avg_hops = sum(hop_counts) / len(hop_counts)
            if avg_hops <= 1.5:
                insights.append("Most paths are short (1-2 hops), indicating direct relationships between guidelines")
            elif avg_hops >= 3:
                insights.append("Paths are relatively long (3+ hops), showing complex interconnected relationships")
            else:
                insights.append("Mixed path lengths suggest both direct and indirect relationships")
        
        # Analyze starting points
        starting_nodes = {}
        for path_result in paths:
            path = path_result.get('path', [])
            if path:
                start_id = path[0].get('id', 'unknown')
                starting_nodes[start_id] = starting_nodes.get(start_id, 0) + 1
        
        if starting_nodes:
            most_common_start = max(starting_nodes.items(), key=lambda x: x[1])
            insights.append(f"Most common starting point: {most_common_start[1]} paths from guideline {most_common_start[0]}")
        
        # Analyze similarities
        similarities = [p.get('start_similarity', 0) for p in paths if p.get('start_similarity')]
        if similarities:
            avg_similarity = sum(similarities) / len(similarities)
            if avg_similarity > 0.5:
                insights.append("High semantic similarity suggests strong relevance to the query")
            elif avg_similarity < 0.3:
                insights.append("Lower semantic similarity - results may be more broadly related")
        
        # Analyze relationship diversity
        all_relationships = []
        for path_result in paths:
            relationships = path_result.get('relationships', [])
            all_relationships.extend([r.get('type', 'Unknown') for r in relationships if isinstance(r, dict)])
        
        if all_relationships:
            unique_relationships = set(all_relationships)
            if len(unique_relationships) > 3:
                insights.append(f"Diverse relationship types ({len(unique_relationships)}) indicate rich knowledge graph connections")
            else:
                insights.append("Limited relationship types - consider expanding the knowledge graph")
        
        return insights

    def _get_used_strategies(self, results: List[Dict], limit: int) -> List[str]:
        """Track which search strategies were used based on results"""
        strategies_used = []
        
        # Check if we have results from semantic search (high similarity)
        high_similarity_results = [r for r in results if r.get('start_similarity', 0) > 0.4]
        if high_similarity_results:
            strategies_used.append("semantic_similarity")
        
        # Check if we have results from fallback search (low similarity)
        low_similarity_results = [r for r in results if r.get('start_similarity', 0) <= 0.3]
        if low_similarity_results:
            strategies_used.append("fallback_search")
        
        # Check if we have results from connected guidelines (very low similarity)
        very_low_similarity_results = [r for r in results if r.get('start_similarity', 0) <= 0.2]
        if very_low_similarity_results:
            strategies_used.append("connected_guidelines")
        
        # If we have results but no clear strategy indicators, assume decomposition was used
        if results and not strategies_used:
            strategies_used.append("query_decomposition")
        
        return strategies_used

    def context_search(self, query: str, limit: int = 5, include_metadata: bool = True) -> List[Dict[str, Any]]:
        """Gather context around guidelines containing the query with enhanced analysis"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (g:Guideline)
                WHERE g.content CONTAINS $query
                WITH g
                OPTIONAL MATCH (g)-[r1:PREREQUISITE]->(prereq:Guideline)
                OPTIONAL MATCH (g)-[r2:EXCEPTION]->(except:Guideline)
                OPTIONAL MATCH (g)-[r3:RELATED]->(related:Guideline)
                WITH g, 
                     collect(DISTINCT {guideline: prereq, relationship: 'PREREQUISITE'}) as prerequisites,
                     collect(DISTINCT {guideline: except, relationship: 'EXCEPTION'}) as exceptions,
                     collect(DISTINCT {guideline: related, relationship: 'RELATED'}) as related_guidelines
                RETURN g, prerequisites, exceptions, related_guidelines
                LIMIT $limit
                """,
                query=query,
                limit=limit
            )
            # Process results and exclude embeddings while keeping essential context
            processed_results = []
            for record in result:
                guideline_data = dict(record["g"])
                
                # Remove embedding to reduce response size
                if "embedding" in guideline_data:
                    del guideline_data["embedding"]
                
                # Keep essential fields that help the LLM
                processed_guideline = {
                    "id": guideline_data.get("id"),
                    "title": guideline_data.get("title"),
                    "content": guideline_data.get("content"),
                    "section": guideline_data.get("section"),
                    "subsection": guideline_data.get("subsection"),
                    "category": guideline_data.get("category"),
                    "source": guideline_data.get("source"),
                    "version": guideline_data.get("version"),
                    "last_updated": guideline_data.get("last_updated"),
                    "priority": guideline_data.get("priority"),
                    "applicability": guideline_data.get("applicability")
                }
                
                # Remove None values
                processed_guideline = {k: v for k, v in processed_guideline.items() if v is not None}
                
                # Process context items to exclude embeddings
                processed_context = {
                    "prerequisites": [],
                    "exceptions": [],
                    "related_guidelines": []
                }
                
                for context_type in ["prerequisites", "exceptions", "related_guidelines"]:
                    for item in record[context_type]:
                        if item.get("guideline"):
                            context_guideline = dict(item["guideline"])
                            if "embedding" in context_guideline:
                                del context_guideline["embedding"]
                            
                            processed_context_item = {
                                "id": context_guideline.get("id"),
                                "title": context_guideline.get("title"),
                                "content": context_guideline.get("content"),
                                "section": context_guideline.get("section"),
                                "subsection": context_guideline.get("subsection"),
                                "category": context_guideline.get("category"),
                                "source": context_guideline.get("source"),
                                "relationship": item.get("relationship")
                            }
                            
                            # Remove None values
                            processed_context_item = {k: v for k, v in processed_context_item.items() if v is not None}
                            processed_context[context_type].append(processed_context_item)
                
                result_item = {
                    "guideline": processed_guideline,
                    "context": processed_context,
                    "metadata": {
                        "category": guideline_data.get("category", "Unknown"),
                        "source": guideline_data.get("source", "Unknown")
                    } if include_metadata else {}
                }
                
                processed_results.append(result_item)
            
            return processed_results

    def get_guideline_by_id(self, guideline_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific guideline by ID"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (g:Guideline {id: $id})
                RETURN g
                """,
                id=guideline_id
            )
            record = result.single()
            return dict(record["g"]) if record else None 

    def analyze_relationships(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Analyze relationships between guidelines"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (g1:Guideline)-[r]->(g2:Guideline)
                WHERE g1.content CONTAINS $query OR g2.content CONTAINS $query
                WITH g1, g2, r, type(r) as rel_type
                OPTIONAL MATCH (g1)-[r2]->(g2)
                WITH g1, g2, r, rel_type, count(r2) as relationship_strength
                RETURN g1, g2, rel_type, relationship_strength
                ORDER BY relationship_strength DESC
                LIMIT $limit
                """,
                query=query,
                limit=limit
            )
            # Process results and exclude embeddings while keeping essential context
            processed_results = []
            for record in result:
                # Process source guideline
                source_guideline_data = dict(record["g1"])
                if "embedding" in source_guideline_data:
                    del source_guideline_data["embedding"]
                
                processed_source_guideline = {
                    "id": source_guideline_data.get("id"),
                    "title": source_guideline_data.get("title"),
                    "content": source_guideline_data.get("content"),
                    "section": source_guideline_data.get("section"),
                    "subsection": source_guideline_data.get("subsection"),
                    "category": source_guideline_data.get("category"),
                    "source": source_guideline_data.get("source"),
                    "version": source_guideline_data.get("version"),
                    "last_updated": source_guideline_data.get("last_updated"),
                    "priority": source_guideline_data.get("priority"),
                    "applicability": source_guideline_data.get("applicability")
                }
                processed_source_guideline = {k: v for k, v in processed_source_guideline.items() if v is not None}
                
                # Process target guideline
                target_guideline_data = dict(record["g2"])
                if "embedding" in target_guideline_data:
                    del target_guideline_data["embedding"]
                
                processed_target_guideline = {
                    "id": target_guideline_data.get("id"),
                    "title": target_guideline_data.get("title"),
                    "content": target_guideline_data.get("content"),
                    "section": target_guideline_data.get("section"),
                    "subsection": target_guideline_data.get("subsection"),
                    "category": target_guideline_data.get("category"),
                    "source": target_guideline_data.get("source"),
                    "version": target_guideline_data.get("version"),
                    "last_updated": target_guideline_data.get("last_updated"),
                    "priority": target_guideline_data.get("priority"),
                    "applicability": target_guideline_data.get("applicability")
                }
                processed_target_guideline = {k: v for k, v in processed_target_guideline.items() if v is not None}
                
                result_item = {
                    "source_guideline": processed_source_guideline,
                    "target_guideline": processed_target_guideline,
                    "type": record["rel_type"],
                    "strength": record["relationship_strength"]
                }
                
                processed_results.append(result_item)
            
            return processed_results

    def get_ai_recommendations(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get AI-powered recommendations based on guidelines"""
        # First get relevant guidelines
        relevant_guidelines = self.semantic_search(query, limit=limit)
        
        if not relevant_guidelines:
            return []
        
        # Use OpenAI to generate recommendations
        guidelines_text = "\n".join([
            f"Guideline {i+1}: {g['guideline'].get('title', 'Unknown')}\n{g['guideline'].get('content', '')}"
            for i, g in enumerate(relevant_guidelines)
        ])
        
        prompt = f"""
        Based on the following mortgage lending guidelines, provide actionable recommendations for: {query}
        
        Guidelines:
        {guidelines_text}
        
        Provide recommendations in JSON format with the following structure:
        {{
            "recommendations": [
                {{
                    "title": "Recommendation title",
                    "description": "Detailed description",
                    "actionability_score": 0.0-1.0,
                    "priority": "high/medium/low",
                    "type": "compliance/risk_mitigation/process_improvement",
                    "related_guidelines": ["guideline_ids"]
                }}
            ]
        }}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert mortgage underwriter providing actionable recommendations."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            recommendations = response.choices[0].message.content
            import json
            return json.loads(recommendations).get("recommendations", [])
        except Exception as e:
            logger.error(f"Failed to generate AI recommendations: {str(e)}")
            return []

    def get_graph_structure(self, query: str, max_depth: int = 3) -> Dict[str, Any]:
        """Get knowledge graph structure around a query"""
        with self.driver.session() as session:
            # Get nodes and edges around the query
            result = session.run(
                f"""
                MATCH (g:Guideline)
                WHERE g.content CONTAINS $query OR g.title CONTAINS $query
                WITH g
                MATCH path = (g)-[*0..{max_depth}]-(related:Guideline)
                WITH collect(DISTINCT nodes(path)) as all_nodes, collect(DISTINCT relationships(path)) as all_edges
                UNWIND all_nodes as nodes
                UNWIND nodes as node
                WITH collect(DISTINCT node) as unique_nodes, all_edges
                UNWIND all_edges as edges
                UNWIND edges as edge
                WITH unique_nodes, collect(DISTINCT edge) as unique_edges
                RETURN unique_nodes, unique_edges
                """,
                query=query
            )
            
            record = result.single()
            if not record:
                return {"nodes": [], "edges": [], "node_count": 0, "edge_count": 0}
            
            # Process nodes to exclude embeddings while keeping essential context
            processed_nodes = []
            for node in record["unique_nodes"]:
                node_data = dict(node)
                
                # Remove embedding to reduce response size
                if "embedding" in node_data:
                    del node_data["embedding"]
                
                # Keep essential fields that help the LLM
                processed_node = {
                    "id": node_data.get("id"),
                    "title": node_data.get("title"),
                    "content": node_data.get("content"),
                    "section": node_data.get("section"),
                    "subsection": node_data.get("subsection"),
                    "category": node_data.get("category"),
                    "source": node_data.get("source"),
                    "version": node_data.get("version"),
                    "last_updated": node_data.get("last_updated"),
                    "priority": node_data.get("priority"),
                    "applicability": node_data.get("applicability")
                }
                
                # Remove None values
                processed_node = {k: v for k, v in processed_node.items() if v is not None}
                processed_nodes.append(processed_node)
            
            edges = [{"source": edge.start_node["id"], "target": edge.end_node["id"], "type": edge.type} for edge in record["unique_edges"]]
            
            # Calculate graph metrics
            node_count = len(processed_nodes)
            edge_count = len(edges)
            density = edge_count / (node_count * (node_count - 1)) if node_count > 1 else 0
            
            # Calculate centrality (simplified)
            centrality = {}
            for node in processed_nodes:
                node_id = node["id"]
                centrality[node_id] = len([e for e in edges if e["source"] == node_id or e["target"] == node_id])
            
            return {
                "nodes": processed_nodes,
                "edges": edges,
                "node_count": node_count,
                "edge_count": edge_count,
                "density": density,
                "centrality": centrality,
                "communities": self._detect_communities(processed_nodes, edges)
            }

    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the knowledge graph"""
        with self.driver.session() as session:
            # Basic counts
            stats = session.run("""
                MATCH (g:Guideline)
                RETURN count(g) as total_guidelines
            """).single()
            
            # Relationship counts
            rel_stats = session.run("""
                MATCH ()-[r]->()
                RETURN count(r) as total_relationships
            """).single()
            
            # Categories
            categories = session.run("""
                MATCH (g:Guideline)
                WHERE g.category IS NOT NULL
                RETURN collect(DISTINCT g.category) as categories
            """).single()
            
            # Sources
            sources = session.run("""
                MATCH (g:Guideline)
                WHERE g.source IS NOT NULL
                RETURN collect(DISTINCT g.source) as sources
            """).single()
            
            # Relationship types
            rel_types = session.run("""
                MATCH ()-[r]->()
                RETURN collect(DISTINCT type(r)) as relationship_types
            """).single()
            
            # Most connected guidelines
            most_connected = session.run("""
                MATCH (g:Guideline)-[r]-()
                WITH g, count(r) as connection_count
                ORDER BY connection_count DESC
                LIMIT 10
                RETURN collect({id: g.id, title: g.title, connections: connection_count}) as most_connected
            """).single()
            
            # Knowledge coverage
            coverage = session.run("""
                MATCH (g:Guideline)
                WITH g,
                     CASE WHEN g.content CONTAINS 'credit' THEN 1 ELSE 0 END as credit,
                     CASE WHEN g.content CONTAINS 'income' THEN 1 ELSE 0 END as income,
                     CASE WHEN g.content CONTAINS 'property' THEN 1 ELSE 0 END as property,
                     CASE WHEN g.content CONTAINS 'document' THEN 1 ELSE 0 END as documentation
                RETURN sum(credit) as credit_count,
                       sum(income) as income_count,
                       sum(property) as property_count,
                       sum(documentation) as doc_count
            """).single()
            
            return {
                "total_guidelines": stats["total_guidelines"],
                "total_relationships": rel_stats["total_relationships"],
                "categories": categories["categories"] if categories["categories"] else [],
                "sources": sources["sources"] if sources["sources"] else [],
                "relationship_types": rel_types["relationship_types"] if rel_types["relationship_types"] else [],
                "density": rel_stats["total_relationships"] / (stats["total_guidelines"] * (stats["total_guidelines"] - 1)) if stats["total_guidelines"] > 1 else 0,
                "avg_connectivity": rel_stats["total_relationships"] / stats["total_guidelines"] if stats["total_guidelines"] > 0 else 0,
                "most_connected": most_connected["most_connected"] if most_connected["most_connected"] else [],
                "recent_updates": [],  # Placeholder for future implementation
                "coverage": {
                    "credit": coverage["credit_count"],
                    "income": coverage["income_count"],
                    "property": coverage["property_count"],
                    "documentation": coverage["doc_count"]
                }
            }

    def _detect_communities(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, List[str]]:
        """Simple community detection based on connected components"""
        # Create adjacency list
        graph = {}
        for node in nodes:
            graph[node["id"]] = []
        
        for edge in edges:
            if edge["source"] in graph:
                graph[edge["source"]].append(edge["target"])
            if edge["target"] in graph:
                graph[edge["target"]].append(edge["source"])
        
        # Find connected components
        visited = set()
        communities = {}
        community_id = 0
        
        for node_id in graph:
            if node_id not in visited:
                community = []
                stack = [node_id]
                while stack:
                    current = stack.pop()
                    if current not in visited:
                        visited.add(current)
                        community.append(current)
                        for neighbor in graph[current]:
                            if neighbor not in visited:
                                stack.append(neighbor)
                
                if len(community) > 1:  # Only include communities with multiple nodes
                    communities[f"community_{community_id}"] = community
                    community_id += 1
        
        return communities

    def _analyze_query_intent(self, query: str) -> Dict:
        """Analyze query intent to understand what the user is looking for"""
        query_lower = query.lower()
        
        # Define intent patterns
        intent_patterns = {
            "comparison": ["compare", "difference", "versus", "vs", "between", "how do", "affect"],
            "definition": ["what is", "define", "meaning", "explain", "describe"],
            "procedure": ["how to", "steps", "process", "procedure", "requirements", "documentation"],
            "analysis": ["analyze", "evaluate", "assess", "review", "examine"],
            "relationship": ["relationship", "connection", "interact", "depend", "influence"],
            "specific": ["specific", "particular", "exact", "precise", "detailed"]
        }
        
        # Count matches for each intent
        intent_scores = {}
        for intent, patterns in intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in query_lower)
            intent_scores[intent] = score
        
        # Determine primary intent
        primary_intent = max(intent_scores.items(), key=lambda x: x[1])
        
        # Analyze complexity
        word_count = len(query.split())
        complexity = "simple" if word_count <= 5 else "moderate" if word_count <= 10 else "complex"
        
        # Check for specific domains
        domains = {
            "credit": ["credit", "score", "fico", "creditworthiness"],
            "income": ["income", "salary", "employment", "earnings", "wages"],
            "property": ["property", "home", "house", "real estate", "collateral"],
            "documentation": ["document", "paperwork", "verification", "proof", "evidence"],
            "approval": ["approval", "approve", "accept", "reject", "decision"]
        }
        
        detected_domains = []
        for domain, keywords in domains.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_domains.append(domain)
        
        return {
            "type": primary_intent[0] if primary_intent[1] > 0 else "general",
            "confidence": primary_intent[1] / max(len(query.split()), 1),
            "complexity": complexity,
            "word_count": word_count,
            "domains": detected_domains,
            "intent_scores": intent_scores
        }

    def _calculate_dynamic_hops(self, query: str, query_intent: Dict, original_max_hops: int) -> int:
        """Calculate dynamic hop limits based on query complexity and intent"""
        base_hops = original_max_hops
        
        # Adjust based on complexity
        complexity_multiplier = {
            "simple": 0.8,
            "moderate": 1.0,
            "complex": 1.3
        }
        
        # Adjust based on intent
        intent_multiplier = {
            "comparison": 1.2,  # Need more hops for comparisons
            "relationship": 1.4,  # Need more hops for relationship analysis
            "analysis": 1.3,  # Need more hops for detailed analysis
            "procedure": 1.1,  # Moderate hops for procedures
            "definition": 0.9,  # Fewer hops for definitions
            "specific": 1.2,  # More hops for specific queries
            "general": 1.0
        }
        
        # Adjust based on domain count
        domain_multiplier = 1.0 + (len(query_intent.get("domains", [])) * 0.1)
        
        # Calculate dynamic hops
        dynamic_hops = int(base_hops * 
                          complexity_multiplier.get(query_intent["complexity"], 1.0) *
                          intent_multiplier.get(query_intent["type"], 1.0) *
                          domain_multiplier)
        
        # Ensure reasonable bounds
        dynamic_hops = max(2, min(dynamic_hops, 6))  # Between 2 and 6 hops
        
        return dynamic_hops

    def _enhance_paths_with_relationships(self, results: List[Dict], session) -> List[Dict]:
        """Enhance paths with better relationship detection"""
        enhanced_results = []
        
        for result in results:
            path = result.get('path', [])
            if len(path) < 2:
                enhanced_results.append(result)
                continue
            
            # Get enhanced relationships for this path
            enhanced_relationships = self._get_enhanced_relationships(path, session)
            
            # Create enhanced result
            enhanced_result = result.copy()
            enhanced_result['relationships'] = enhanced_relationships
            enhanced_result['relationship_insights'] = self._analyze_relationships_for_path(enhanced_relationships)
            
            enhanced_results.append(enhanced_result)
        
        return enhanced_results

    def _get_enhanced_relationships(self, path: List[Dict], session) -> List[Dict]:
        """Get enhanced relationships between nodes in a path"""
        relationships = []
        
        for i in range(len(path) - 1):
            node1_id = path[i].get('id')
            node2_id = path[i + 1].get('id')
            
            if not node1_id or not node2_id:
                continue
            
            # Query for relationships between these nodes
            rel_result = session.run(
                """
                MATCH (g1:Guideline {id: $node1_id})-[r]-(g2:Guideline {id: $node2_id})
                RETURN type(r) as rel_type, properties(r) as rel_props
                """,
                node1_id=node1_id,
                node2_id=node2_id
            ).data()
            
            for rel in rel_result:
                relationships.append({
                    "type": rel["rel_type"],
                    "properties": rel["rel_props"],
                    "source_node": node1_id,
                    "target_node": node2_id,
                    "step": i + 1
                })
            
            # If no direct relationship found, try to infer one
            if not rel_result:
                inferred_rel = self._infer_relationship(path[i], path[i + 1])
                if inferred_rel:
                    relationships.append({
                        "type": inferred_rel["type"],
                        "properties": {"inferred": True, "confidence": inferred_rel["confidence"]},
                        "source_node": node1_id,
                        "target_node": node2_id,
                        "step": i + 1
                    })
        
        return relationships

    def _infer_relationship(self, node1: Dict, node2: Dict) -> Optional[Dict]:
        """Infer relationship between two nodes based on content analysis"""
        content1 = node1.get('content', '').lower()
        content2 = node2.get('content', '').lower()
        
        # Define relationship patterns
        relationship_patterns = {
            "PREREQUISITE": ["before", "required", "prerequisite", "must have", "needed"],
            "RELATED": ["related", "similar", "associated", "connected"],
            "EXCEPTION": ["except", "exception", "unless", "however", "but"],
            "ENHANCES": ["improves", "enhances", "strengthens", "supports"],
            "CONFLICTS": ["conflicts", "contradicts", "opposes", "disagrees"]
        }
        
        # Check for relationship indicators in content
        for rel_type, patterns in relationship_patterns.items():
            for pattern in patterns:
                if pattern in content1 or pattern in content2:
                    return {
                        "type": rel_type,
                        "confidence": 0.6  # Moderate confidence for inferred relationships
                    }
        
        # Check for semantic similarity
        if self._calculate_content_similarity(content1, content2) > 0.3:
            return {
                "type": "RELATED",
                "confidence": 0.4
            }
        
        return None

    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate simple content similarity based on common words"""
        words1 = set(content1.split())
        words2 = set(content2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

    def _analyze_relationships_for_path(self, relationships: List[Dict]) -> Dict:
        """Analyze relationships in a path to provide insights"""
        if not relationships:
            return {"insights": ["No explicit relationships found"], "strength": 0.0}
        
        # Count relationship types
        rel_types = {}
        for rel in relationships:
            rel_type = rel.get('type', 'Unknown')
            rel_types[rel_type] = rel_types.get(rel_type, 0) + 1
        
        # Calculate relationship strength
        total_rels = len(relationships)
        inferred_rels = sum(1 for rel in relationships if rel.get('properties', {}).get('inferred', False))
        strength = (total_rels - inferred_rels * 0.5) / total_rels if total_rels > 0 else 0.0
        
        insights = []
        if inferred_rels > 0:
            insights.append(f"{inferred_rels} inferred relationships out of {total_rels} total")
        
        if len(rel_types) > 1:
            insights.append(f"Diverse relationship types: {list(rel_types.keys())}")
        
        if strength > 0.8:
            insights.append("Strong explicit relationships")
        elif strength > 0.5:
            insights.append("Moderate relationship strength")
        else:
            insights.append("Weak or inferred relationships")
        
        return {
            "insights": insights,
            "strength": strength,
            "relationship_types": rel_types,
            "total_relationships": total_rels,
            "inferred_relationships": inferred_rels
        }

    def _score_path_quality(self, results: List[Dict], query_intent: Dict) -> List[Dict]:
        """Score path quality based on multiple factors"""
        scored_results = []
        
        for result in results:
            score = 0.0
            scoring_factors = {}
            
            # Factor 1: Semantic similarity of starting node
            start_similarity = result.get('start_similarity', 0)
            score += start_similarity * 0.3
            scoring_factors['semantic_similarity'] = start_similarity
            
            # Factor 2: Path length appropriateness
            hop_count = result.get('hop_count', 0)
            optimal_hops = 2 if query_intent['complexity'] == 'simple' else 3
            hop_score = 1.0 - abs(hop_count - optimal_hops) * 0.2
            hop_score = max(0.0, hop_score)
            score += hop_score * 0.2
            scoring_factors['path_length'] = hop_score
            
            # Factor 3: Relationship strength
            rel_insights = result.get('relationship_insights', {})
            rel_strength = rel_insights.get('strength', 0)
            score += rel_strength * 0.25
            scoring_factors['relationship_strength'] = rel_strength
            
            # Factor 4: Domain relevance
            path_domains = self._extract_domains_from_path(result.get('path', []))
            query_domains = query_intent.get('domains', [])
            domain_overlap = len(set(path_domains) & set(query_domains))
            domain_score = min(domain_overlap / max(len(query_domains), 1), 1.0)
            score += domain_score * 0.15
            scoring_factors['domain_relevance'] = domain_score
            
            # Factor 5: Content richness
            path = result.get('path', [])
            content_length = sum(len(node.get('content', '')) for node in path)
            content_score = min(content_length / 10000, 1.0)  # Normalize to 10k chars
            score += content_score * 0.1
            scoring_factors['content_richness'] = content_score
            
            # Ensure score is between 0 and 1
            score = max(0.0, min(1.0, score))
            
            # Add scoring information to result
            scored_result = result.copy()
            scored_result['quality_score'] = score
            scored_result['scoring_factors'] = scoring_factors
            scored_result['quality_level'] = self._get_quality_level(score)
            
            scored_results.append(scored_result)
        
        # Sort by quality score (highest first)
        scored_results.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        return scored_results

    def _extract_domains_from_path(self, path: List[Dict]) -> List[str]:
        """Extract domains from path content"""
        domains = {
            "credit": ["credit", "score", "fico", "creditworthiness", "credit report"],
            "income": ["income", "salary", "employment", "earnings", "wages", "pay"],
            "property": ["property", "home", "house", "real estate", "collateral", "appraisal"],
            "documentation": ["document", "paperwork", "verification", "proof", "evidence", "file"],
            "approval": ["approval", "approve", "accept", "reject", "decision", "underwriting"]
        }
        
        path_domains = []
        path_content = " ".join([node.get('content', '').lower() for node in path])
        
        for domain, keywords in domains.items():
            if any(keyword in path_content for keyword in keywords):
                path_domains.append(domain)
        
        return path_domains

    def _get_quality_level(self, score: float) -> str:
        """Convert quality score to quality level"""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        else:
            return "poor"

    def _get_path_quality_stats(self, results: List[Dict]) -> Dict:
        """Get statistics about path quality"""
        if not results:
            return {}
        
        scores = [r.get('quality_score', 0) for r in results]
        quality_levels = [r.get('quality_level', 'unknown') for r in results]
        
        return {
            "avg_quality_score": sum(scores) / len(scores),
            "min_quality_score": min(scores),
            "max_quality_score": max(scores),
            "quality_distribution": {
                "excellent": quality_levels.count("excellent"),
                "good": quality_levels.count("good"),
                "fair": quality_levels.count("fair"),
                "poor": quality_levels.count("poor")
            },
            "high_quality_paths": len([s for s in scores if s >= 0.7])
        } 