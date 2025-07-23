import unittest
from app.services.semantic_search import SemanticSearchService
from app.models.loan_application import LoanApplication, Borrower, Property, LoanDetails, Employment
from datetime import datetime

class TestSemanticSearch(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.semantic_search = SemanticSearchService()
        
        # Create a test loan application
        self.test_application = LoanApplication(
            id=1,
            borrowers=[
                Borrower(
                    first_name="John",
                    last_name="Doe",
                    annual_income=120000,
                    monthly_debts=2000,
                    employment=Employment(
                        employer_name="Tech Corp",
                        years_employed=5
                    )
                )
            ],
            property=Property(
                property_type="Single Family",
                estimated_value=400000,
                down_payment=80000
            ),
            loan_details=LoanDetails(
                loan_amount=320000,
                interest_rate=0.035,
                loan_term=30
            ),
            credit_score=750
        )
    
    def test_basic_search(self):
        """Test basic semantic search functionality."""
        query = "What are the guidelines for conventional loans with 20% down payment?"
        results = self.semantic_search.search(query, top_k=3)
        
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 3)
        
        for result in results:
            self.assertIn('content', result)
            self.assertIn('similarity_score', result)
            self.assertIsInstance(result['similarity_score'], float)
            self.assertGreaterEqual(result['similarity_score'], 0)
            self.assertLessEqual(result['similarity_score'], 1)
    
    def test_search_with_context(self):
        """Test semantic search with additional context."""
        query = "DTI requirements"
        context = "Conventional loan with 20% down payment"
        results = self.semantic_search.search_with_context(query, context, top_k=3)
        
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 3)
        
        for result in results:
            self.assertIn('content', result)
            self.assertIn('similarity_score', result)
    
    def test_application_specific_search(self):
        """Test semantic search with loan application details."""
        # Create a search query based on application details
        query = f"""
        Loan application with:
        - Credit Score: {self.test_application.credit_score}
        - DTI Ratio: {self.test_application.monthly_debt / (self.test_application.annual_income / 12):.2%}
        - LTV Ratio: {self.test_application.loan_amount / self.test_application.property_value:.2%}
        - Property Type: {self.test_application.property_type}
        - Down Payment: {self.test_application.down_payment / self.test_application.property_value:.2%}
        """
        
        results = self.semantic_search.search(query, top_k=5)
        
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 5)
        
        # Verify that results are relevant to the application
        for result in results:
            self.assertIn('content', result)
            self.assertIn('similarity_score', result)
            # Check if the content contains relevant terms
            content = result['content'].lower()
            relevant_terms = ['conventional', 'loan', 'guidelines', 'requirements']
            self.assertTrue(any(term in content for term in relevant_terms))

if __name__ == '__main__':
    unittest.main() 