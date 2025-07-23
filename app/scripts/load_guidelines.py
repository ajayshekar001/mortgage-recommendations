import json
from datetime import datetime
from app.db.session import SessionLocal
from app.models.knowledge_graph import GuidelineNode
from app.services.knowledge_service import KnowledgeService
from app.models.loan_application import LoanApplication

def load_guidelines():
    """Load Fannie Mae guidelines into the knowledge graph"""
    db = SessionLocal()
    knowledge_service = KnowledgeService()
    
    try:
        # Comprehensive Fannie Mae guidelines
        guidelines = [
            {
                "title": "Maximum DTI Ratio",
                "content": "The maximum total debt-to-income (DTI) ratio is 43% of the borrower's stable monthly income. The maximum front-end ratio is 28%. For loans with compensating factors, DTI up to 45% may be considered.",
                "category": "DTI",
                "source": "Fannie Mae",
                "version": "B5-6.2-01",
                "effective_date": datetime(2023, 1, 1),
                "metadata": {
                    "max_dti": 0.43,
                    "max_front_end": 0.28,
                    "max_dti_with_compensating": 0.45
                }
            },
            {
                "title": "Minimum Credit Score",
                "content": "The minimum credit score for a conventional loan is 620. For loans with LTV ratios greater than 80%, a minimum credit score of 680 is required. For loans with multiple risk factors, a minimum score of 700 is recommended.",
                "category": "Credit",
                "source": "Fannie Mae",
                "version": "B3-5.3-01",
                "effective_date": datetime(2023, 1, 1),
                "metadata": {
                    "min_score": 620,
                    "min_score_high_ltv": 680,
                    "min_score_multiple_risk": 700
                }
            },
            {
                "title": "Maximum LTV Ratio",
                "content": "The maximum loan-to-value (LTV) ratio is 97% for first-time homebuyers and 95% for other borrowers. For cash-out refinances, the maximum LTV is 80%.",
                "category": "LTV",
                "source": "Fannie Mae",
                "version": "B5-6.2-02",
                "effective_date": datetime(2023, 1, 1),
                "metadata": {
                    "max_ltv_first_time": 0.97,
                    "max_ltv_other": 0.95,
                    "max_ltv_cash_out": 0.80
                }
            },
            {
                "title": "Reserves Requirements",
                "content": "For loans with LTV ratios greater than 80%, borrowers must have reserves equal to 2 months of PITI. For loans with DTI ratios greater than 43%, 6 months of reserves are required.",
                "category": "Reserves",
                "source": "Fannie Mae",
                "version": "B3-4.1-01",
                "effective_date": datetime(2023, 1, 1),
                "metadata": {
                    "reserves_high_ltv": 2,
                    "reserves_high_dti": 6
                }
            },
            {
                "title": "Employment Requirements",
                "content": "Borrowers must have a two-year history of employment in the same line of work. Gaps in employment must be explained and documented.",
                "category": "Employment",
                "source": "Fannie Mae",
                "version": "B3-3.1-01",
                "effective_date": datetime(2023, 1, 1),
                "metadata": {
                    "min_employment_years": 2
                }
            },
            {
                "title": "Income Documentation Requirements",
                "content": "For salaried borrowers, provide W-2s and pay stubs. For self-employed, provide 2 years of tax returns and YTD P&L. For commissioned income, provide 2 years of tax returns and 12 months of commission statements.",
                "category": "Income",
                "source": "Fannie Mae",
                "version": "B3-3.1-02",
                "effective_date": datetime(2023, 1, 1),
                "metadata": {
                    "salaried_docs": ["W2", "PayStub"],
                    "self_employed_docs": ["TaxReturn", "P&L"],
                    "commissioned_docs": ["TaxReturn", "CommissionStatement"]
                }
            },
            {
                "title": "Asset Documentation Requirements",
                "content": "Provide 2 months of bank statements for all accounts. For large deposits, provide source documentation. For retirement accounts, provide most recent statement and verification of vested balance.",
                "category": "Assets",
                "source": "Fannie Mae",
                "version": "B3-4.1-02",
                "effective_date": datetime(2023, 1, 1),
                "metadata": {
                    "required_months": 2,
                    "large_deposit_threshold": 10000
                }
            },
            {
                "title": "Property Requirements",
                "content": "Property must be in good condition and meet minimum property requirements. For condos, the project must be warrantable. For manufactured homes, must be on permanent foundation and meet HUD requirements.",
                "category": "Property",
                "source": "Fannie Mae",
                "version": "B2-2-01",
                "effective_date": datetime(2023, 1, 1),
                "metadata": {
                    "min_property_standards": "good_condition",
                    "condo_requirements": "warrantable",
                    "manufactured_home_requirements": ["permanent_foundation", "hud_compliant"]
                }
            },
            {
                "title": "Compensating Factors",
                "content": "Strong compensating factors may allow for more flexible underwriting. Factors include: large down payment (25%+), significant reserves (12+ months), excellent credit (760+), low DTI (36% or less), stable employment (5+ years).",
                "category": "Underwriting",
                "source": "Fannie Mae",
                "version": "B5-6.2-03",
                "effective_date": datetime(2023, 1, 1),
                "metadata": {
                    "compensating_factors": {
                        "large_down_payment": 0.25,
                        "significant_reserves": 12,
                        "excellent_credit": 760,
                        "low_dti": 0.36,
                        "stable_employment": 5
                    }
                }
            },
            {
                "title": "Loan Program Requirements",
                "content": "Conventional loans require 3% down payment for first-time buyers, 5% for others. FHA loans require 3.5% down payment. VA loans allow 0% down payment for eligible veterans. USDA loans allow 0% down payment in eligible rural areas.",
                "category": "Loan Programs",
                "source": "Fannie Mae",
                "version": "B5-6.2-04",
                "effective_date": datetime(2023, 1, 1),
                "metadata": {
                    "conventional_first_time": 0.03,
                    "conventional_other": 0.05,
                    "fha": 0.035,
                    "va": 0.0,
                    "usda": 0.0
                }
            },
            {
                "title": "Risk Assessment Framework",
                "content": "Evaluate applications based on: credit profile, income stability, property type, loan characteristics, and market conditions. Higher risk in any area requires stronger compensating factors in others.",
                "category": "Risk Assessment",
                "source": "Fannie Mae",
                "version": "B5-6.2-05",
                "effective_date": datetime(2023, 1, 1),
                "metadata": {
                    "risk_factors": [
                        "credit_profile",
                        "income_stability",
                        "property_type",
                        "loan_characteristics",
                        "market_conditions"
                    ]
                }
            }
        ]
        
        # Create guideline nodes
        for guideline in guidelines:
            # Create a minimal LoanApplication object for embedding
            application = LoanApplication(
                borrower_name="GuidelineBot",
                credit_score=guideline["metadata"].get("min_score", 700),
                annual_income=guideline["metadata"].get("min_income", 100000),
                loan_amount=guideline["metadata"].get("min_loan_amount", 100000),
                property_value=guideline["metadata"].get("min_property_value", 100000),
                down_payment=guideline["metadata"].get("min_down_payment", 20000),
                loan_term_years=30,
                interest_rate=0.035,
                monthly_debt=guideline["metadata"].get("min_monthly_debt", 1000),
                employment_status=None,
                years_employed=guideline["metadata"].get("min_employment_years", 2),
                employer_name="GuidelineBot",
                job_title="N/A",
                monthly_income=guideline["metadata"].get("min_income", 100000) // 12
            )
            embedding = knowledge_service._create_application_embedding(application)
            
            # Create guideline node
            node = GuidelineNode(
                title=guideline["title"],
                content=guideline["content"],
                category=guideline["category"],
                source=guideline["source"],
                version=guideline["version"],
                effective_date=guideline["effective_date"],
                guideline_metadata=guideline["metadata"],
                embedding=embedding
            )
            
            db.add(node)
        
        db.commit()
        print("Successfully loaded guidelines into the knowledge graph")
        
    except Exception as e:
        print(f"Error loading guidelines: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    load_guidelines() 