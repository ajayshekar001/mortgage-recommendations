import pytest
from datetime import date
from app.models.loan_application import LoanApplication, Borrower, Property, LoanDetails, Document
from app.services.loan_validator import LoanValidator

@pytest.fixture
def sample_application():
    return LoanApplication(
        application_id="TEST-001",
        borrowers=[
            Borrower(
                first_name="John",
                last_name="Doe",
                ssn="123-45-6789",
                date_of_birth=date(1980, 1, 1),
                current_address="123 Main St",
                employment_status="Employed",
                annual_income=100000.0,
                monthly_debts=2000.0
            )
        ],
        property=Property(
            address="456 Oak St",
            property_type="Single Family",
            estimated_value=500000.0,
            purchase_price=450000.0,
            down_payment=45000.0
        ),
        loan_details=LoanDetails(
            loan_amount=405000.0,
            loan_type="Conventional",
            loan_term=30,
            interest_rate=0.045,
            property_taxes=5000.0,
            insurance=1200.0
        ),
        documents=[
            Document(
                document_type="W2",
                file_name="w2_2023.pdf",
                upload_date=date(2024, 1, 1)
            )
        ],
        credit_score=700
    )

def test_dti_calculation(sample_application):
    validator = LoanValidator()
    dti = validator.calculate_dti(sample_application)
    assert dti == pytest.approx(0.24)  # 2000 / (100000/12)

def test_ltv_calculation(sample_application):
    validator = LoanValidator()
    ltv = validator.calculate_ltv(sample_application)
    assert ltv == pytest.approx(0.81)  # 405000 / 500000

def test_validation_approval(sample_application):
    validator = LoanValidator()
    result = validator.validate_application(sample_application)
    assert result.is_approved == True
    assert len(result.risk_flags) == 0

def test_validation_high_dti():
    # Create application with high DTI
    application = LoanApplication(
        application_id="TEST-002",
        borrowers=[
            Borrower(
                first_name="Jane",
                last_name="Smith",
                ssn="987-65-4321",
                date_of_birth=date(1985, 1, 1),
                current_address="789 Pine St",
                employment_status="Employed",
                annual_income=60000.0,
                monthly_debts=3000.0
            )
        ],
        property=Property(
            address="321 Elm St",
            property_type="Single Family",
            estimated_value=300000.0,
            purchase_price=280000.0,
            down_payment=28000.0
        ),
        loan_details=LoanDetails(
            loan_amount=252000.0,
            loan_type="Conventional",
            loan_term=30,
            interest_rate=0.045,
            property_taxes=3000.0,
            insurance=800.0
        ),
        documents=[],
        credit_score=650
    )
    
    validator = LoanValidator()
    result = validator.validate_application(application)
    assert result.is_approved == False
    assert 'high_dti' in result.risk_flags
    assert len(result.recommendations) > 0

def test_missing_documents(sample_application):
    # Remove all documents
    sample_application.documents = []
    
    validator = LoanValidator()
    result = validator.validate_application(sample_application)
    assert result.is_approved == False
    assert 'missing_docs' in result.risk_flags
    assert any("documentation" in rec for rec in result.recommendations) 