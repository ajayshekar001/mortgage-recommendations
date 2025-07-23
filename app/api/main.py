from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import json
import os
from datetime import datetime
import uuid
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.services.pdf_processor import PDFProcessor
from app.services.loan_validator import LoanValidator
from app.services.loan_converter import LoanConverter
from app.services.neo4j_knowledge_graph import Neo4jKnowledgeGraph
from app.models.loan_application import LoanApplication, ValidationResult
from app.models.external_loan_application import ExternalLoanApplication

app = FastAPI(
    title="Loan Application Processing System",
    description="API for processing loan applications and validating documents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        raise

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class KnowledgeGraphQuery(BaseModel):
    query: str
    search_type: str = "semantic"  # semantic, multi_hop, context, relationships, recommendations, graph_structure
    max_results: int = 5
    max_hops: Optional[int] = 3
    include_metadata: bool = True
    include_relationships: bool = True
    filter_category: Optional[str] = None
    filter_source: Optional[str] = None

class ComparisonQuery(BaseModel):
    query: str
    max_results: int = 8
    max_hops: int = 4
    include_chain_of_thought: bool = True

loan_converter = LoanConverter()
loan_validator = LoanValidator()

@app.post("/process-documents")
async def process_documents(
    files: List[UploadFile] = File(...),
    document_types: List[str] = None
):
    """
    Process uploaded loan documents and convert them to URLA format
    """
    logger.info(f"Processing {len(files)} documents")
    if not document_types or len(document_types) != len(files):
        raise HTTPException(status_code=400, detail="Document types must be provided for each file")
    
    results = []
    for file, doc_type in zip(files, document_types):
        # Save file temporarily
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
        try:
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Process the document
            extracted_data = pdf_processor.process_document(file_path, doc_type)
            mismo_data = pdf_processor.extract_to_mismo(extracted_data, doc_type)
            
            results.append({
                "filename": file.filename,
                "document_type": doc_type,
                "extracted_data": extracted_data,
                "mismo_format": mismo_data
            })
            
        except Exception as e:
            logger.error(f"Error processing {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing {file.filename}: {str(e)}")
        finally:
            # Clean up temporary file
            if os.path.exists(file_path):
                os.remove(file_path)
    
    return {"processed_documents": results}

@app.post("/validate-application")
async def validate_application(application_data: ExternalLoanApplication):
    """
    Validate loan application data against underwriting rules
    """
    try:
        # Get borrower name from the application data
        borrower_name = f"{application_data.loanApplication['borrower']['firstName']} {application_data.loanApplication['borrower']['lastName']}"
        logger.info(f"=== Starting validation for borrower: {borrower_name} ===")
        
        # Log input data summary
        loan_data = application_data.loanApplication['loan']
        borrower_data = application_data.loanApplication['borrower']
        logger.info(f"Input Summary - Loan Amount: ${loan_data['loanAmount']:,.2f}, Property Value: ${loan_data['propertyValue']:,.2f}")
        logger.info(f"Input Summary - Annual Income: ${borrower_data['income']['base']:,.2f}, Monthly Debt: ${sum(liability['monthlyPayment'] for liability in borrower_data['liabilities']):,.2f}")
        
        # Convert external format to internal model
        logger.info("Converting external application format to internal model...")
        internal_application = loan_converter.convert_to_internal(application_data)
        logger.info(f"Conversion complete - Internal ID: {internal_application.id}")
        logger.info(f"Converted Data - Annual Income: ${internal_application.annual_income:,.2f}, Monthly Debt: ${internal_application.monthly_debt:,.2f}")
        
        # Calculate key metrics before validation
        dti_ratio = loan_validator.calculate_dti(internal_application)
        ltv_ratio = loan_validator.calculate_ltv(internal_application)
        logger.info(f"Pre-validation Metrics - DTI: {dti_ratio:.2%}, LTV: {ltv_ratio:.2%}")
        
        # Validate the application
        logger.info("Starting application validation...")
        validation_result = loan_validator.validate_application(internal_application)
        
        # Log validation results
        logger.info(f"=== Validation Results for {borrower_name} ===")
        logger.info(f"Approval Decision: {'APPROVED' if validation_result.is_approved else 'REJECTED'}")
        logger.info(f"Risk Score: {validation_result.risk_score:.3f}")
        logger.info(f"Risk Flags: {validation_result.risk_flags}")
        logger.info(f"Number of Recommendations: {len(validation_result.recommendations)}")
        logger.info(f"Explanation: {validation_result.explanation}")
        
        # Log final metrics
        if hasattr(validation_result, 'dti_ratio') and validation_result.dti_ratio:
            logger.info(f"Final DTI Ratio: {validation_result.dti_ratio:.2%}")
        if hasattr(validation_result, 'ltv_ratio') and validation_result.ltv_ratio:
            logger.info(f"Final LTV Ratio: {validation_result.ltv_ratio:.2%}")
        
        logger.info(f"=== Validation complete for {borrower_name} ===")
        return validation_result.to_dict()
    
    except Exception as e:
        logger.error(f"Validation failed for application: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.post("/query-knowledge-graph")
async def query_knowledge_graph(query_data: KnowledgeGraphQuery):
    """
    Enhanced knowledge graph query endpoint showcasing the power of the knowledge graph
    
    Search Types:
    - semantic: Find relevant guidelines using semantic similarity
    - multi_hop: Discover connections between guidelines through multiple hops
    - context: Gather comprehensive context around a topic
    - relationships: Analyze relationships between guidelines
    - recommendations: Get AI-powered recommendations based on guidelines
    - graph_structure: Visualize the knowledge graph structure
    """
    logger.info(f"Enhanced knowledge graph query: {query_data.search_type} - {query_data.query}")
    
    try:
        with Neo4jKnowledgeGraph() as kg:
            if not kg.verify_connection():
                raise HTTPException(status_code=503, detail="Neo4j connection is not available")
            
            # Add filters if specified
            filters = {}
            if query_data.filter_category:
                filters['category'] = query_data.filter_category
            if query_data.filter_source:
                filters['source'] = query_data.filter_source
            
            if query_data.search_type == "semantic":
                # Enhanced semantic search with metadata
                results = kg.semantic_search(
                    query_data.query, 
                    limit=query_data.max_results,
                    include_metadata=query_data.include_metadata
                )
                logger.info(f"Semantic search found {len(results)} results")
                
                # Add search insights
                search_insights = {
                    "query_similarity_scores": [result.get('similarity', 0) for result in results],
                    "top_categories": list(set([result.get('guideline', {}).get('category', 'Unknown') for result in results])),
                    "coverage_analysis": f"Found guidelines covering {len(set([result.get('guideline', {}).get('category', 'Unknown') for result in results]))} different categories"
                }
                
                return {
                    "search_type": "semantic",
                    "query": query_data.query,
                    "results": results,
                    "search_insights": search_insights,
                    "total_results": len(results),
                    "filters_applied": filters
                }
                
            elif query_data.search_type == "multi_hop":
                # Enhanced multi-hop search with comprehensive path analysis
                search_result = kg.multi_hop_search(
                    query_data.query,
                    max_hops=query_data.max_hops,
                    limit=query_data.max_results,
                    include_relationships=query_data.include_relationships
                )
                
                # Extract components from the new response format
                results = search_result.get("paths", [])
                path_analysis = search_result.get("path_analysis", {})
                search_metadata = search_result.get("search_metadata", {})
                
                logger.info(f"Multi-hop search found {len(results)} paths using strategies: {search_metadata.get('search_strategies_used', [])}")
                
                return {
                    "search_type": "multi_hop",
                    "query": query_data.query,
                    "max_hops": query_data.max_hops,
                    "results": results,
                    "path_analysis": path_analysis,
                    "search_metadata": search_metadata,
                    "total_paths": len(results),
                    "filters_applied": filters
                }
                    
            elif query_data.search_type == "context":
                # Enhanced context search with comprehensive analysis
                results = kg.context_search(
                    query_data.query, 
                    limit=query_data.max_results,
                    include_metadata=query_data.include_metadata
                )
                logger.info(f"Context search found {len(results)} results")
                
                # Context analysis
                context_analysis = {
                    "prerequisites_count": sum(len(result.get('context', {}).get('prerequisites', [])) for result in results),
                    "exceptions_count": sum(len(result.get('context', {}).get('exceptions', [])) for result in results),
                    "related_guidelines_count": sum(len(result.get('context', {}).get('related_guidelines', [])) for result in results),
                    "context_depth": "Comprehensive context gathered including prerequisites, exceptions, and related guidelines"
                }
                
                return {
                    "search_type": "context",
                    "query": query_data.query,
                    "results": results,
                    "context_analysis": context_analysis,
                    "total_context_items": len(results),
                    "filters_applied": filters
                }
            
            elif query_data.search_type == "relationships":
                # Analyze relationships between guidelines
                results = kg.analyze_relationships(
                    query_data.query,
                    limit=query_data.max_results
                )
                logger.info(f"Relationship analysis found {len(results)} relationship patterns")
                
                # Relationship insights
                relationship_insights = {
                    "strongest_relationships": sorted(results, key=lambda x: x.get('strength', 0), reverse=True)[:3],
                    "relationship_types": list(set([rel.get('type', 'Unknown') for rel in results])),
                    "network_density": f"Found {len(results)} relationship patterns with average strength {sum(r.get('strength', 0) for r in results) / len(results):.2f}"
                }
                
                return {
                    "search_type": "relationships",
                    "query": query_data.query,
                    "results": results,
                    "relationship_insights": relationship_insights,
                    "total_relationships": len(results),
                    "filters_applied": filters
                }
            
            elif query_data.search_type == "recommendations":
                # Get AI-powered recommendations based on guidelines
                results = kg.get_ai_recommendations(
                    query_data.query,
                    limit=query_data.max_results
                )
                logger.info(f"AI recommendations generated {len(results)} suggestions")
                
                # Recommendation analysis
                recommendation_analysis = {
                    "actionable_items": len([r for r in results if r.get('actionability_score', 0) > 0.7]),
                    "priority_levels": {
                        "high": len([r for r in results if r.get('priority', 'medium') == 'high']),
                        "medium": len([r for r in results if r.get('priority', 'medium') == 'medium']),
                        "low": len([r for r in results if r.get('priority', 'medium') == 'low'])
                    },
                    "recommendation_types": list(set([r.get('type', 'Unknown') for r in results]))
                }
                
                return {
                    "search_type": "recommendations",
                    "query": query_data.query,
                    "results": results,
                    "recommendation_analysis": recommendation_analysis,
                    "total_recommendations": len(results),
                    "filters_applied": filters
                }
            
            elif query_data.search_type == "graph_structure":
                # Visualize knowledge graph structure
                results = kg.get_graph_structure(
                    query_data.query,
                    max_depth=query_data.max_hops
                )
                logger.info(f"Graph structure analysis completed")
                
                # Structure analysis
                structure_analysis = {
                    "total_nodes": results.get('node_count', 0),
                    "total_edges": results.get('edge_count', 0),
                    "centrality_metrics": results.get('centrality', {}),
                    "community_detection": results.get('communities', {}),
                    "graph_density": results.get('density', 0)
                }
                
                return {
                    "search_type": "graph_structure",
                    "query": query_data.query,
                    "results": results,
                    "structure_analysis": structure_analysis,
                    "graph_metrics": {
                        "nodes": results.get('nodes', []),
                        "edges": results.get('edges', []),
                        "communities": results.get('communities', {})
                    },
                    "filters_applied": filters
                }
            
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid search type: {query_data.search_type}. Must be one of: semantic, multi_hop, context, relationships, recommendations, graph_structure"
                )
                
    except Exception as e:
        logger.error(f"Knowledge graph query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compare-query-approaches")
async def compare_query_approaches(query_data: ComparisonQuery):
    """
    Compare three different approaches to answering the same query:
    1. Direct LLM - Pure LLM response without knowledge base
    2. Semantic Search + LLM - Semantic search results polished by LLM
    3. Multi-hop Chain of Thought + LLM - Multi-hop search with chain-of-thought reasoning polished by LLM
    
    This endpoint showcases the power of knowledge graphs and chain-of-thought reasoning.
    """
    logger.info(f"Comparing query approaches for: {query_data.query}")
    
    try:
        with Neo4jKnowledgeGraph() as kg:
            if not kg.verify_connection():
                raise HTTPException(status_code=503, detail="Neo4j connection is not available")
            
            comparison_results = {}
            
            # 1. Direct LLM Approach
            logger.info("Executing Direct LLM approach...")
            direct_llm_response = await _get_direct_llm_response(query_data.query)
            comparison_results["direct_llm"] = {
                "approach": "Direct LLM",
                "description": "Pure LLM response without any knowledge base or external data",
                "response": direct_llm_response,
                "metadata": {
                    "response_length": len(direct_llm_response),
                    "approach_type": "pure_llm",
                    "knowledge_source": "none"
                }
            }
            
            # 2. Semantic Search + LLM Approach
            logger.info("Executing Semantic Search + LLM approach...")
            semantic_results = kg.semantic_search(
                query_data.query,
                limit=query_data.max_results,
                include_metadata=True
            )
            semantic_llm_response = await _get_semantic_llm_response(
                query_data.query, 
                semantic_results
            )
            comparison_results["semantic_llm"] = {
                "approach": "Semantic Search + LLM",
                "description": "Semantic search results from knowledge graph polished by LLM",
                "knowledge_base_results": semantic_results,
                "response": semantic_llm_response,
                "metadata": {
                    "guidelines_found": len(semantic_results),
                    "avg_similarity": sum(r.get('similarity', 0) for r in semantic_results) / len(semantic_results) if semantic_results else 0,
                    "response_length": len(semantic_llm_response),
                    "approach_type": "semantic_search_llm",
                    "knowledge_source": "semantic_search"
                }
            }
            
            # 3. Multi-hop Chain of Thought + LLM Approach
            logger.info("Executing Multi-hop Chain of Thought + LLM approach...")
            multi_hop_search_result = kg.multi_hop_search(
                query_data.query,
                max_hops=query_data.max_hops,
                limit=query_data.max_results,
                include_relationships=True
            )
            
            # Extract paths from the new response format
            multi_hop_results = multi_hop_search_result.get("paths", [])
            path_analysis = multi_hop_search_result.get("path_analysis", {})
            search_metadata = multi_hop_search_result.get("search_metadata", {})
            
            chain_of_thought_response = await _get_chain_of_thought_response(
                query_data.query,
                multi_hop_results,
                query_data.include_chain_of_thought
            )
            comparison_results["multi_hop_chain_of_thought"] = {
                "approach": "Multi-hop Chain of Thought + LLM",
                "description": "Multi-hop search with chain-of-thought reasoning polished by LLM",
                "knowledge_base_results": multi_hop_results,
                "path_analysis": path_analysis,
                "search_metadata": search_metadata,
                "response": chain_of_thought_response,
                "metadata": {
                    "paths_found": len(multi_hop_results),
                    "max_hops_explored": query_data.max_hops,
                    "avg_path_length": sum(r.get('hop_count', 0) for r in multi_hop_results) / len(multi_hop_results) if multi_hop_results else 0,
                    "response_length": len(chain_of_thought_response),
                    "approach_type": "multi_hop_chain_of_thought",
                    "knowledge_source": "multi_hop_search",
                    "chain_of_thought_enabled": query_data.include_chain_of_thought,
                    "search_strategies_used": search_metadata.get("search_strategies_used", [])
                }
            }
            
            # Generate comparison analysis
            comparison_analysis = await _generate_comparison_analysis(
                query_data.query,
                comparison_results
            )
            
            return {
                "query": query_data.query,
                "comparison_results": comparison_results,
                "comparison_analysis": comparison_analysis,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "total_approaches": 3,
                    "max_results_per_approach": query_data.max_results,
                    "max_hops_explored": query_data.max_hops,
                    "evaluation_included": True,
                    "evaluation_criteria": [
                        "accuracy", "completeness", "relevance", "specificity", "practical_value"
                    ]
                },
                "evaluation_summary": {
                    "best_approach": comparison_analysis.get("overall_analysis", {}).get("best_approach", "unknown"),
                    "key_insights": comparison_analysis.get("overall_analysis", {}).get("key_insights", []),
                    "scores_summary": {
                        approach: {
                            "overall_score": comparison_analysis.get("detailed_evaluation", {}).get(f"approach_{i+1}", {}).get("overall_score", 0.0),
                            "accuracy_score": comparison_analysis.get("detailed_evaluation", {}).get(f"approach_{i+1}", {}).get("accuracy_score", 0.0),
                            "completeness_score": comparison_analysis.get("detailed_evaluation", {}).get(f"approach_{i+1}", {}).get("completeness_score", 0.0),
                            "practical_value_score": comparison_analysis.get("detailed_evaluation", {}).get(f"approach_{i+1}", {}).get("practical_value_score", 0.0)
                        }
                        for i, approach in enumerate(comparison_results.keys())
                    }
                }
            }
            
    except Exception as e:
        logger.error(f"Query comparison failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def _get_direct_llm_response(query: str) -> str:
    """Get direct LLM response without any knowledge base"""
    try:
        from openai import OpenAI
        import os
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        prompt = f"""
        You are an expert mortgage underwriter. Answer the following question based on your general knowledge:
        
        Question: {query}
        
        Provide a comprehensive, accurate response. If you're not certain about specific details, acknowledge the limitations of your knowledge.
        """
        
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert mortgage underwriter with extensive knowledge of lending guidelines and regulations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Direct LLM response failed: {str(e)}")
        return f"Error generating direct LLM response: {str(e)}"

async def _get_semantic_llm_response(query: str, semantic_results: List[Dict]) -> str:
    """Get LLM response based on semantic search results"""
    try:
        from openai import OpenAI
        import os
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Format semantic search results
        guidelines_text = ""
        for i, result in enumerate(semantic_results):
            guideline = result.get('guideline', {})
            guidelines_text += f"\nGuideline {i+1} (Similarity: {result.get('similarity', 0):.3f}):\n"
            guidelines_text += f"Title: {guideline.get('title', 'Unknown')}\n"
            guidelines_text += f"Content: {guideline.get('content', '')[:500]}...\n"
        
        prompt = f"""
        You are an expert mortgage underwriter. Answer the following question based on the provided guidelines from our knowledge base:
        
        Question: {query}
        
        Relevant Guidelines from Knowledge Base:
        {guidelines_text}
        
        Provide a comprehensive answer that:
        1. Directly addresses the question
        2. References specific guidelines when applicable
        3. Acknowledges the source of information (knowledge base vs general knowledge)
        4. Highlights any limitations or areas where additional information might be needed
        """
        
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert mortgage underwriter. Use the provided guidelines to give accurate, well-referenced responses."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1200,
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Semantic LLM response failed: {str(e)}")
        return f"Error generating semantic LLM response: {str(e)}"

async def _get_chain_of_thought_response(query: str, multi_hop_results: List[Dict], include_chain_of_thought: bool) -> str:
    """Get LLM response based on multi-hop search with chain-of-thought reasoning"""
    try:
        from openai import OpenAI
        import os
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Format multi-hop results with chain-of-thought structure
        knowledge_graph_text = ""
        chain_of_thought_text = ""
        
        if include_chain_of_thought:
            chain_of_thought_text = """
            Chain of Thought Analysis:
            Let me trace through the knowledge graph connections to understand the relationships between different guidelines and how they connect to answer this question.
            """
        
        for i, path_result in enumerate(multi_hop_results):
            path = path_result.get('path', [])
            hop_count = path_result.get('hop_count', 0)
            
            knowledge_graph_text += f"\nPath {i+1} ({hop_count} hops):\n"
            
            if include_chain_of_thought:
                knowledge_graph_text += f"Chain of Thought: Following this {hop_count}-hop path reveals connections between:\n"
            
            for j, node in enumerate(path):
                knowledge_graph_text += f"  Step {j+1}: {node.get('title', 'Unknown')}\n"
                if include_chain_of_thought and j < len(path) - 1:
                    knowledge_graph_text += f"    → Connected to next guideline via relationship\n"
            
            knowledge_graph_text += f"  Key Insights: {path_result.get('relationships', [])}\n"
        
        prompt = f"""
        You are an expert mortgage underwriter with access to a sophisticated knowledge graph. Answer the following question using chain-of-thought reasoning based on the multi-hop search results:
        
        Question: {query}
        
        {chain_of_thought_text}
        
        Knowledge Graph Analysis:
        {knowledge_graph_text}
        
        Provide a comprehensive answer that demonstrates:
        1. Chain-of-thought reasoning showing how you connected different pieces of information
        2. How the multi-hop paths reveal deeper insights than simple keyword matching
        3. Specific references to the knowledge graph connections
        4. The value of exploring relationships between guidelines
        5. Any limitations or areas where the knowledge graph could be expanded
        """
        
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert mortgage underwriter skilled in chain-of-thought reasoning and knowledge graph analysis."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Chain of thought response failed: {str(e)}")
        return f"Error generating chain of thought response: {str(e)}"

async def _generate_comparison_analysis(query: str, comparison_results: Dict) -> Dict:
    """Generate comprehensive analysis comparing the three approaches with LLM-based accuracy assessment"""
    try:
        from openai import OpenAI
        import os
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Prepare detailed comparison data with full responses
        approaches_data = []
        for approach_name, data in comparison_results.items():
            approaches_data.append({
                "name": data["approach"],
                "description": data["description"],
                "full_response": data["response"],
                "response_length": data["metadata"]["response_length"],
                "knowledge_source": data["metadata"]["knowledge_source"],
                "approach_type": data["metadata"]["approach_type"],
                "additional_metadata": data.get("metadata", {})
            })
        
        # Create detailed prompt for comprehensive evaluation
        evaluation_prompt = f"""
        You are an expert mortgage underwriter and AI evaluation specialist. Perform a comprehensive analysis of three different approaches to answering the same mortgage underwriting question.

        QUESTION: {query}

        APPROACHES TO EVALUATE:
        """
        
        for i, approach in enumerate(approaches_data, 1):
            evaluation_prompt += f"""
        APPROACH {i}: {approach['name']}
        Description: {approach['description']}
        Knowledge Source: {approach['knowledge_source']}
        Response Length: {approach['response_length']} characters
        
        FULL RESPONSE:
        {approach['full_response']}
        
        ---
        """
        
        evaluation_prompt += """
        
        Please provide a comprehensive evaluation in JSON format with the following structure:
        {
            "overall_analysis": {
                "summary": "Brief summary of the comparison",
                "best_approach": "name of the best performing approach",
                "key_insights": ["list of key insights about the approaches"]
            },
            "detailed_evaluation": {
                "approach_1": {
                    "accuracy_score": 0.0-1.0,
                    "completeness_score": 0.0-1.0,
                    "relevance_score": 0.0-1.0,
                    "specificity_score": 0.0-1.0,
                    "practical_value_score": 0.0-1.0,
                    "overall_score": 0.0-1.0,
                    "strengths": ["list of strengths"],
                    "weaknesses": ["list of weaknesses"],
                    "accuracy_assessment": "detailed assessment of factual accuracy",
                    "completeness_assessment": "assessment of how complete the answer is",
                    "relevance_assessment": "assessment of relevance to the question",
                    "specificity_assessment": "assessment of specific details and examples",
                    "practical_value_assessment": "assessment of practical value for underwriters"
                },
                "approach_2": { ... same structure as approach_1 ... },
                "approach_3": { ... same structure as approach_1 ... }
            },
            "comparative_analysis": {
                "accuracy_comparison": "detailed comparison of accuracy across approaches",
                "completeness_comparison": "detailed comparison of completeness across approaches",
                "knowledge_utilization": "analysis of how well each approach uses available knowledge",
                "reasoning_quality": "comparison of reasoning quality and logical flow",
                "practical_applicability": "comparison of practical value for real-world use"
            },
            "recommendations": {
                "best_for_accuracy": "which approach is best for accuracy",
                "best_for_completeness": "which approach is best for completeness",
                "best_for_practical_use": "which approach is best for practical underwriting",
                "when_to_use_each": {
                    "approach_1": "when to use this approach",
                    "approach_2": "when to use this approach", 
                    "approach_3": "when to use this approach"
                },
                "improvement_suggestions": ["suggestions for improving each approach"]
            }
        }
        
        EVALUATION CRITERIA:
        1. ACCURACY (0.0-1.0): Factual correctness, adherence to mortgage guidelines, absence of errors
        2. COMPLETENESS (0.0-1.0): Coverage of all relevant aspects, depth of analysis, comprehensiveness
        3. RELEVANCE (0.0-1.0): Direct relevance to the question, focus on key issues
        4. SPECIFICITY (0.0-1.0): Specific details, examples, guideline references, concrete information
        5. PRACTICAL VALUE (0.0-1.0): Usability for underwriters, actionable insights, real-world applicability
        
        Be thorough and objective in your evaluation. Consider the unique strengths and limitations of each approach.
        """
        
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert mortgage underwriter and AI evaluation specialist with deep knowledge of mortgage guidelines, underwriting processes, and AI systems. Provide objective, thorough evaluations."},
                {"role": "user", "content": evaluation_prompt}
            ],
            max_tokens=3000,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        # Parse the JSON response
        import json
        evaluation_result = json.loads(response.choices[0].message.content)
        
        # Add metadata about the evaluation
        evaluation_result["evaluation_metadata"] = {
            "evaluation_timestamp": datetime.utcnow().isoformat(),
            "evaluation_model": "gpt-4-turbo-preview",
            "evaluation_criteria": [
                "accuracy", "completeness", "relevance", "specificity", "practical_value"
            ],
            "total_approaches_evaluated": len(approaches_data),
            "query_analyzed": query
        }
        
        # Add approach comparison summary
        approach_comparison = {
            "response_lengths": {data["name"]: data["response_length"] for data in approaches_data},
            "knowledge_sources": {data["name"]: data["knowledge_source"] for data in approaches_data},
            "approach_types": {data["name"]: data["approach_type"] for data in approaches_data}
        }
        
        evaluation_result["approach_comparison"] = approach_comparison
        
        return evaluation_result
        
    except Exception as e:
        logger.error(f"Comprehensive comparison analysis failed: {str(e)}")
        return {
            "overall_analysis": {
                "summary": f"Error generating comprehensive analysis: {str(e)}",
                "best_approach": "unknown",
                "key_insights": ["Analysis failed due to technical error"]
            },
            "detailed_evaluation": {},
            "comparative_analysis": {},
            "recommendations": {},
            "evaluation_metadata": {
                "error": str(e),
                "evaluation_timestamp": datetime.utcnow().isoformat()
            },
            "approach_comparison": {}
        }

@app.get("/knowledge-graph-stats")
async def get_knowledge_graph_stats():
    """
    Get comprehensive statistics about the knowledge graph
    """
    try:
        with Neo4jKnowledgeGraph() as kg:
            if not kg.verify_connection():
                raise HTTPException(status_code=503, detail="Neo4j connection is not available")
            
            stats = kg.get_graph_statistics()
            return {
                "total_guidelines": stats.get('total_guidelines', 0),
                "total_relationships": stats.get('total_relationships', 0),
                "categories": stats.get('categories', []),
                "sources": stats.get('sources', []),
                "relationship_types": stats.get('relationship_types', []),
                "graph_density": stats.get('density', 0),
                "average_connectivity": stats.get('avg_connectivity', 0),
                "most_connected_guidelines": stats.get('most_connected', []),
                "recent_updates": stats.get('recent_updates', []),
                "knowledge_coverage": {
                    "credit_analysis": stats.get('coverage', {}).get('credit', 0),
                    "income_verification": stats.get('coverage', {}).get('income', 0),
                    "property_requirements": stats.get('coverage', {}).get('property', 0),
                    "documentation": stats.get('coverage', {}).get('documentation', 0)
                }
            }
    except Exception as e:
        logger.error(f"Failed to get knowledge graph stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 