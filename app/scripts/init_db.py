from app.db.session import engine
from app.db.base_class import Base
from app.models.loan_application import LoanApplication, ValidationResult
from app.models.knowledge_graph import GuidelineNode, GuidelineApplication
from app.models.decision_history import DecisionHistory

def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    init_db() 