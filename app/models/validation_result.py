from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class ValidationResult(Base):
    __tablename__ = "validation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("loan_applications.id"))
    approved = Column(Boolean)
    risk_score = Column(Float)
    risk_flags = Column(JSON)  # List of risk flags
    recommendations = Column(JSON)  # List of recommendations
    explanation = Column(String)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    
    # Relationship
    application = relationship("LoanApplication", back_populates="validation_results")
    
    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "approved": self.approved,
            "risk_score": self.risk_score,
            "risk_flags": self.risk_flags,
            "recommendations": self.recommendations,
            "explanation": self.explanation,
            "created_at": self.created_at
        } 