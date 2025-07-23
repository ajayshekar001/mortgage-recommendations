from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime

class DecisionHistory(Base):
    __tablename__ = "decision_history"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Application details
    credit_score = Column(Integer)
    annual_income = Column(Float)
    loan_amount = Column(Float)
    property_value = Column(Float)
    dti_ratio = Column(Float)
    ltv_ratio = Column(Float)
    
    # Decision details
    is_approved = Column(Integer)  # 0 or 1
    risk_score = Column(Float)
    risk_factors = Column(JSON)  # List of risk factors
    recommendations = Column(JSON)  # List of recommendations
    
    # Additional metadata
    property_type = Column(String)
    employment_years = Column(Integer)
    down_payment = Column(Float)
    
    # Vector embedding for similarity search
    embedding = Column(JSON)  # Will store vector embeddings for similarity search 