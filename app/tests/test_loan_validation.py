import unittest
from datetime import datetime
from app.models.loan_application import LoanApplication, EmploymentType
from app.services.loan_validator import LoanValidator
from app.services.knowledge_service import KnowledgeService
from app.db.session import SessionLocal
from app.scripts.load_guidelines import load_guidelines

class TestLoanValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment before running tests."""
        # Load guidelines into the knowledge graph
        load_guidelines()
        
        # Initialize services
        cls.validator = LoanValidator()
        cls.knowledge_service = KnowledgeService()
        
        # Create database session
        cls.db = SessionLocal()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests."""
        cls.db.close()
    
    def create_test_application(self, **kwargs):
        """Helper method to create a test loan application."""
        default_values = {
            "borrower_name": "John Doe",
            "credit_score": 750,
            "annual_income": 120000,
            "loan_amount": 300000,
            "property_value": 400000,
            "down_payment": 100000,
            "loan_term_years": 30,
            "interest_rate": 0.035,
            "monthly_debt": 2000,
            "employment_status": EmploymentType.FULL_TIME,
            "years_employed": 5,
            "employer_name": "Tech Corp",
            "job_title": "Software Engineer",
            "monthly_income": 10000
        }
        
        # Update with any provided values
        default_values.update(kwargs)
        
        # Create and return the application
        application = LoanApplication(**default_values)
        self.db.add(application)
        self.db.commit()
        return application
    
    def test_ideal_application(self):
        """Test an ideal loan application that should be approved."""
        application = self.create_test_application(
            credit_score=750,
            annual_income=120000,
            loan_amount=300000,
            property_value=400000,
            down_payment=100000,
            monthly_debt=2000
        )
        result = self.validator.validate_application(application)
        self.assertTrue(result.is_approved)
    
    def test_high_dti_application(self):
        """Test an application with high DTI ratio."""
        application = self.create_test_application(
            credit_score=700,
            annual_income=60000,
            loan_amount=300000,
            property_value=400000,
            down_payment=100000,
            monthly_debt=3000
        )
        result = self.validator.validate_application(application)
        self.assertFalse(result.is_approved)
    
    def test_low_credit_score(self):
        """Test an application with low credit score."""
        application = self.create_test_application(
            credit_score=580,
            annual_income=120000,
            loan_amount=300000,
            property_value=400000,
            down_payment=100000,
            monthly_debt=2000
        )
        result = self.validator.validate_application(application)
        self.assertFalse(result.is_approved)
    
    def test_high_ltv_application(self):
        """Test an application with high LTV ratio."""
        application = self.create_test_application(
            credit_score=700,
            annual_income=120000,
            loan_amount=380000,
            property_value=400000,
            down_payment=20000,
            monthly_debt=2000
        )
        result = self.validator.validate_application(application)
        self.assertFalse(result.is_approved)
    
    def test_compensating_factors(self):
        """Test an application with strong compensating factors."""
        application = self.create_test_application(
            credit_score=680,
            annual_income=150000,
            loan_amount=300000,
            property_value=400000,
            down_payment=100000,
            monthly_debt=2500
        )
        result = self.validator.validate_application(application)
        self.assertTrue(result.is_approved)
    
    def test_self_employed_application(self):
        """Test an application for a self-employed borrower."""
        application = self.create_test_application(
            credit_score=720,
            annual_income=100000,
            loan_amount=300000,
            property_value=400000,
            down_payment=100000,
            monthly_debt=2000,
            employment_status=EmploymentType.SELF_EMPLOYED
        )
        result = self.validator.validate_application(application)
        self.assertFalse(result.is_approved)
    
    def test_chain_of_thought_analysis(self):
        """Test the chain-of-thought analysis structure."""
        application = self.create_test_application()
        analysis = self.knowledge_service.analyze_with_guidelines(application)
        
        # Check analysis structure
        self.assertIn("guideline_applications", analysis)
        self.assertIn("overall_analysis", analysis)
        
        # Check guideline applications
        for app in analysis["guideline_applications"]:
            self.assertIn("guideline_id", app)
            self.assertIn("is_applicable", app)
            self.assertIn("reasoning", app)
            self.assertIn("impact", app)
            self.assertIn("confidence", app)
        
        # Check overall analysis
        overall = analysis["overall_analysis"]
        self.assertIn("risk_assessment", overall)
        self.assertIn("approval_decision", overall)
        self.assertIn("key_factors", overall)
        self.assertIn("recommendations", overall["approval_decision"])

if __name__ == "__main__":
    unittest.main() 