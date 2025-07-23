import json
import logging
from pathlib import Path
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.db.session import SessionLocal
from app.models.knowledge_graph import Guideline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_guidelines_to_knowledge_graph():
    """Load Fannie Mae guidelines into the knowledge graph."""
    # Initialize services
    knowledge_service = KnowledgeGraphService()
    db = SessionLocal()
    
    try:
        # Load guidelines from JSON file
        guidelines_path = Path("/Users/shekar/blend/hackathon/uploads/selling_guide_chunks_with_openai_embeddings.json")
        with open(guidelines_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        logger.info(f"Loaded {len(chunks)} guideline chunks")
        
        # Process each chunk
        for chunk in chunks:
            # Extract metadata
            metadata = chunk.get('metadata', {})
            section = metadata.get('section', '')
            subsection = metadata.get('subsection', '')
            
            # Create guideline
            guideline = knowledge_service.add_guideline(
                title=f"{section} - {subsection}" if section and subsection else "Guideline",
                content=chunk['content'],
                section=section,
                subsection=subsection
            )
            
            logger.info(f"Added guideline: {guideline.title}")
        
        # Add relationships between guidelines
        # This is a simplified example - in practice, you'd want to use NLP to identify relationships
        guidelines = db.query(Guideline).all()
        for i, guideline in enumerate(guidelines):
            # Add some example relationships
            if i > 0:
                # Add previous guideline as prerequisite
                knowledge_service.add_relationship(
                    guideline.id,
                    guidelines[i-1].id,
                    'prerequisite'
                )
            
            # Add some related guidelines
            if i > 2:
                knowledge_service.add_relationship(
                    guideline.id,
                    guidelines[i-2].id,
                    'related'
                )
        
        logger.info("Successfully loaded guidelines into knowledge graph")
        
    except Exception as e:
        logger.error(f"Error loading guidelines: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    load_guidelines_to_knowledge_graph() 