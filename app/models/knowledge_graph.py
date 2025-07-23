from typing import List, Dict, Optional
from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime
import numpy as np
import json

# Association table for guideline relationships
guideline_relationships = Table(
    'guideline_relationships',
    Base.metadata,
    Column('source_id', Integer, ForeignKey('guidelines.id')),
    Column('target_id', Integer, ForeignKey('guidelines.id')),
    Column('relationship_type', String(50))  # e.g., 'prerequisite', 'exception', 'related'
)

class Guideline(Base):
    """Model for storing Fannie Mae guidelines with embeddings"""
    __tablename__ = "guidelines"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    content = Column(Text)
    section = Column(String(100), index=True)
    subsection = Column(String(100), index=True)
    embedding = Column(Text)  # Store embedding as JSON string
    
    # Relationships
    prerequisites = relationship(
        "Guideline",
        secondary=guideline_relationships,
        primaryjoin="and_(Guideline.id==guideline_relationships.c.source_id, "
                   "guideline_relationships.c.relationship_type=='prerequisite')",
        secondaryjoin="Guideline.id==guideline_relationships.c.target_id",
        backref="required_by"
    )
    
    exceptions = relationship(
        "Guideline",
        secondary=guideline_relationships,
        primaryjoin="and_(Guideline.id==guideline_relationships.c.source_id, "
                   "guideline_relationships.c.relationship_type=='exception')",
        secondaryjoin="Guideline.id==guideline_relationships.c.target_id",
        backref="excepts"
    )
    
    related_guidelines = relationship(
        "Guideline",
        secondary=guideline_relationships,
        primaryjoin="and_(Guideline.id==guideline_relationships.c.source_id, "
                   "guideline_relationships.c.relationship_type=='related')",
        secondaryjoin="Guideline.id==guideline_relationships.c.target_id",
        backref="related_to"
    )

    def get_embedding_vector(self) -> List[float]:
        """Convert stored embedding string to vector"""
        if not self.embedding:
            return []
        return json.loads(self.embedding)

    def set_embedding_vector(self, vector: List[float]) -> None:
        """Convert vector to string for storage"""
        if not vector:
            self.embedding = None
            return
        self.embedding = json.dumps(vector)

    def to_dict(self) -> Dict:
        """Convert guideline to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "section": self.section,
            "subsection": self.subsection,
            "prerequisites": [p.id for p in self.prerequisites],
            "exceptions": [e.id for e in self.exceptions],
            "related_guidelines": [r.id for r in self.related_guidelines]
        }

class GuidelineNode(Base):
    __tablename__ = "guideline_nodes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    category = Column(String, index=True)  # e.g., 'DTI', 'LTV', 'Credit', 'Income'
    source = Column(String)  # e.g., 'Fannie Mae', 'Freddie Mac'
    version = Column(String)
    effective_date = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships to other guidelines
    related_guidelines = relationship(
        'GuidelineNode',
        secondary=guideline_relationships,
        primaryjoin=id==guideline_relationships.c.source_id,
        secondaryjoin=id==guideline_relationships.c.target_id,
        backref='related_from'
    )
    
    # Additional metadata
    guideline_metadata = Column(JSON)  # For storing additional structured data
    embedding = Column(JSON)  # For semantic search

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "source": self.source,
            "version": self.version,
            "effective_date": str(self.effective_date) if self.effective_date else None,
            "last_updated": str(self.last_updated) if self.last_updated else None,
            "guideline_metadata": self.guideline_metadata,
        }

class GuidelineApplication(Base):
    __tablename__ = "guideline_applications"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String, index=True)
    guideline_id = Column(Integer, ForeignKey('guideline_nodes.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Application of the guideline
    is_applicable = Column(Integer)  # 0 or 1
    reasoning = Column(String)  # Chain of thought reasoning
    impact = Column(String)  # Impact on the decision
    confidence = Column(Float)  # Confidence in the application
    
    # Relationship to the guideline
    guideline = relationship("GuidelineNode") 