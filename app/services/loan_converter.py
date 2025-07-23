from datetime import datetime
from app.models.loan_application import LoanApplication, Borrower, Property, LoanDetails, Document
from app.models.external_loan_application import ExternalLoanApplication

class LoanConverter:
    @staticmethod
    def convert_to_internal(external_app: ExternalLoanApplication):
        """Convert external loan application format to internal model (flat fields)"""
        loan_app = external_app.loanApplication
        borrower_data = loan_app['borrower']
        loan_data = loan_app['loan']
        submission_data = loan_app['submissionMetadata']

        # Calculate total annual income
        total_annual_income = (
            borrower_data['income']['base'] +
            borrower_data['income']['overtime'] +
            borrower_data['income']['bonuses'] +
            borrower_data['income']['otherIncome']
        )
        # Calculate total monthly debt
        total_monthly_debt = sum(liability['monthlyPayment'] for liability in borrower_data['liabilities'])
        # Employment info (use first employment record if available)
        employment = borrower_data['employment'][0] if borrower_data['employment'] else {}
        # Flat property info
        property_value = loan_data['propertyValue']
        loan_amount = loan_data['loanAmount']
        down_payment = property_value - loan_amount
        # Employment status
        employment_status = 'full_time' if employment and not employment.get('selfEmployed', False) else 'self_employed'
        # Years employed (estimate from startDate)
        years_employed = 0.0
        if employment and employment.get('startDate'):
            try:
                start = datetime.strptime(employment['startDate'], '%Y-%m-%d')
                years_employed = (datetime.utcnow() - start).days / 365.25
            except Exception:
                years_employed = 0.0
        # Monthly income (from employment or total annual)
        monthly_income = employment.get('incomeMonthly', total_annual_income / 12) if employment else total_annual_income / 12
        # Compose borrower name
        borrower_name = f"{borrower_data['firstName']} {borrower_data['lastName']}"
        # Compose employer name and job title
        employer_name = employment.get('employerName', '') if employment else ''
        job_title = employment.get('position', '') if employment else ''
        # Compose address (first residence)
        # Not used in flat model, but could be added if needed
        # Compose interest rate (convert to decimal)
        interest_rate = loan_data['interestRate'] / 100 if loan_data['interestRate'] > 1 else loan_data['interestRate']
        
        # Get credit score from borrower data or set reasonable default
        credit_score = borrower_data.get('creditScore', 750)  # Default to 750 if not provided
        
        # Create the internal loan application (flat fields)
        internal_app = LoanApplication(
            id=submission_data['applicationId'],
            borrower_name=borrower_name,
            credit_score=credit_score,  # Use extracted credit score
            annual_income=total_annual_income,
            loan_amount=loan_amount,
            property_value=property_value,
            down_payment=down_payment,
            loan_term_years=loan_data['termMonths'] // 12,
            interest_rate=interest_rate,
            monthly_debt=total_monthly_debt,
            employment_status=employment_status,
            years_employed=years_employed,
            employer_name=employer_name,
            job_title=job_title,
            monthly_income=monthly_income
        )
        return internal_app 