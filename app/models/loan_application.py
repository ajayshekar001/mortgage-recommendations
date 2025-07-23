from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
import enum
from app.db.base_class import Base

class Borrower(BaseModel):
    first_name: str
    last_name: str
    ssn: str
    date_of_birth: date
    current_address: str
    employment_status: str
    annual_income: float
    monthly_debts: float

class Property(BaseModel):
    address: str
    property_type: str
    estimated_value: float
    purchase_price: float
    down_payment: float

class LoanDetails(BaseModel):
    loan_amount: float
    loan_type: str  # e.g., "Conventional", "FHA", "VA"
    loan_term: int  # in years
    interest_rate: float
    property_taxes: float
    insurance: float

class Document(BaseModel):
    document_type: str  # e.g., "W2", "BankStatement", "TaxReturn"
    file_name: str
    upload_date: date
    verification_status: str = "pending"

class EmploymentType(enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    SELF_EMPLOYED = "self_employed"
    RETIRED = "retired"
    UNEMPLOYED = "unemployed"

class Employment(Base):
    __tablename__ = "employment"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("loan_applications.id"))
    employment_type = Column(Enum(EmploymentType))
    employer_name = Column(String)
    job_title = Column(String)
    years_employed = Column(Float)
    monthly_income = Column(Float)
    is_current_employer = Column(Boolean, default=True)
    start_date = Column(String)  # Format: YYYY-MM-DD
    end_date = Column(String, nullable=True)  # Format: YYYY-MM-DD
    
    # Relationship
    application = relationship("LoanApplication", back_populates="employment_history")

class LoanApplication(Base):
    __tablename__ = "loan_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    borrower_name = Column(String, index=True)
    credit_score = Column(Integer)
    annual_income = Column(Float)
    loan_amount = Column(Float)
    property_value = Column(Float)
    down_payment = Column(Float)
    loan_term_years = Column(Integer)
    interest_rate = Column(Float)
    monthly_debt = Column(Float)
    employment_status = Column(Enum(EmploymentType))
    years_employed = Column(Float)
    employer_name = Column(String)
    job_title = Column(String)
    monthly_income = Column(Float)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    
    # Relationships
    employment_history = relationship("Employment", back_populates="application")
    validation_results = relationship("ValidationResult", back_populates="application")
    
    def to_dict(self):
        return {
            "id": self.id,
            "borrower_name": self.borrower_name,
            "credit_score": self.credit_score,
            "annual_income": self.annual_income,
            "loan_amount": self.loan_amount,
            "property_value": self.property_value,
            "down_payment": self.down_payment,
            "loan_term_years": self.loan_term_years,
            "interest_rate": self.interest_rate,
            "monthly_debt": self.monthly_debt,
            "employment_status": self.employment_status.value if self.employment_status else None,
            "years_employed": self.years_employed,
            "employer_name": self.employer_name,
            "job_title": self.job_title,
            "monthly_income": self.monthly_income,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class ValidationResult(Base):
    __tablename__ = "validation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("loan_applications.id"))
    is_approved = Column(Boolean)
    risk_score = Column(Float)
    risk_flags = Column(JSON)
    recommendations = Column(JSON)
    dti_ratio = Column(Float)
    ltv_ratio = Column(Float)
    explanation = Column(String)
    
    # Relationship
    application = relationship("LoanApplication", back_populates="validation_results")

    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "is_approved": self.is_approved,
            "risk_score": self.risk_score,
            "risk_flags": self.risk_flags,
            "recommendations": self.recommendations,
            "dti_ratio": self.dti_ratio,
            "ltv_ratio": self.ltv_ratio,
            "explanation": self.explanation
        } 