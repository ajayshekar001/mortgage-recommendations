from typing import Dict, List, Optional
import google.generativeai as genai
from app.core.config import settings
from app.models.loan_application import LoanApplication, ValidationResult
from app.models.decision_history import DecisionHistory
from app.db.session import SessionLocal
from app.services.knowledge_graph_service import KnowledgeGraphService
from datetime import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging
import json
from openai import OpenAI
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoanAgent:
    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        self.knowledge_service = KnowledgeGraphService()
        self.llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info("Initialized LoanAgent with Gemini model and KnowledgeGraphService")
        
    def analyze_application(self, application: LoanApplication) -> Dict:
        """Analyze loan application using Gemini and knowledge graph"""
        logger.info(f"Starting analysis for application ID: {application.id}")
        
        # Get similar cases for context
        similar_cases = self.get_similar_cases(application)
        logger.info(f"Found {len(similar_cases)} similar cases")
        
        # Get relevant guidelines using knowledge graph
        relevant_guidelines = self._get_relevant_guidelines(application)
        logger.info(f"Found {len(relevant_guidelines)} relevant guidelines")
        
        # Create prompt with similar cases and guidelines context
        prompt = self._create_analysis_prompt(application, similar_cases, relevant_guidelines)
        logger.debug(f"Generated prompt: {prompt}")
        
        response = self.model.generate_content(prompt)
        analysis = response.text
        logger.info("Received response from Gemini model")
        logger.debug(f"Raw analysis: {analysis}")
        
        # Parse the analysis into structured format
        parsed_analysis = self._parse_analysis(analysis)
        logger.info("Successfully parsed analysis")
        return parsed_analysis
    
    def _get_relevant_guidelines(self, application: LoanApplication) -> List[Dict]:
        """Get relevant guidelines using knowledge graph search"""
        # Create a search query based on application details
        query = f"""
        Loan application with:
        - Credit Score: {application.credit_score}
        - DTI Ratio: {self._calculate_dti(application):.2%}
        - LTV Ratio: {self._calculate_ltv(application):.2%}
        - Property Type: {application.property_type}
        - Down Payment: {application.down_payment / application.property_value:.2%}
        """
        
        # Search for relevant guidelines
        results = self.knowledge_service.semantic_search(query, top_k=5)
        
        # Format results for the prompt
        formatted_results = []
        for result in results:
            guideline = result['guideline']
            context = result['context']
            
            formatted_result = {
                'content': guideline['content'],
                'title': guideline['title'],
                'section': guideline['section'],
                'subsection': guideline['subsection'],
                'prerequisites': [p['content'] for p in context['prerequisites']],
                'exceptions': [e['content'] for e in context['exceptions']],
                'related_guidelines': [r['content'] for r in context['related_guidelines']]
            }
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def _create_analysis_prompt(self, application: LoanApplication, similar_cases: List[Dict], relevant_guidelines: List[Dict]) -> str:
        """Create a detailed prompt for loan analysis with similar cases and guidelines context"""
        similar_cases_context = ""
        if similar_cases:
            similar_cases_context = "\n\nSIMILAR PAST CASES:\n"
            for i, case in enumerate(similar_cases, 1):
                similar_cases_context += f"""
                Case {i}:
                - Credit Score: {case.credit_score}
                - Annual Income: ${case.annual_income:,.2f}
                - Loan Amount: ${case.loan_amount:,.2f}
                - DTI Ratio: {case.dti_ratio:.2%}
                - LTV Ratio: {case.ltv_ratio:.2%}
                - Decision: {'Approved' if case.is_approved else 'Denied'}
                - Risk Score: {case.risk_score:.2f}
                - Risk Factors: {', '.join(case.risk_factors)}
                """
        
        guidelines_context = ""
        if relevant_guidelines:
            guidelines_context = "\n\nRELEVANT GUIDELINES:\n"
            for i, guideline in enumerate(relevant_guidelines, 1):
                guidelines_context += f"""
                Guideline {i}: {guideline['title']}
                Content: {guideline['content']}
                
                Prerequisites:
                {chr(10).join(f'- {p}' for p in guideline['prerequisites'])}
                
                Exceptions:
                {chr(10).join(f'- {e}' for e in guideline['exceptions'])}
                
                Related Guidelines:
                {chr(10).join(f'- {r}' for r in guideline['related_guidelines'])}
                """
        
        return f"""
        As an expert mortgage underwriter, analyze this loan application comprehensively:

        BORROWER PROFILE:
        - Credit Score: {application.credit_score}
        - Annual Income: ${application.annual_income:,.2f}
        - Employment: {application.employer_name} ({application.years_employed} years)
        - Monthly Debts: ${application.monthly_debt:,.2f}

        LOAN DETAILS:
        - Amount: ${application.loan_amount:,.2f}
        - Interest Rate: {application.interest_rate:.2%}
        - Term: {application.loan_term_years} years
        - Property Type: {application.property_type}
        - Property Value: ${application.property_value:,.2f}
        - Down Payment: ${application.down_payment:,.2f}

        FINANCIAL METRICS:
        - DTI Ratio: {self._calculate_dti(application):.2%}
        - LTV Ratio: {self._calculate_ltv(application):.2%}
        - Reserves Ratio: {self._calculate_reserves(application):.2f}

        DECLARATIONS:
        - Bankruptcy: {application.declarations.bankruptcy}
        - Foreclosure: {application.declarations.foreclosure}
        - Lawsuit: {application.declarations.lawsuit}
        - Delinquent Debt: {application.declarations.delinquent_debt}
        {similar_cases_context}
        {guidelines_context}

        IMPORTANT CONSTRAINTS:
        - Focus ONLY on core financial metrics: DTI ratio, LTV ratio, credit score, income stability, and employment history
        - DO NOT include document type validations like property_type, market_conditions, asset_documentation, or employment verification
        - DO NOT require additional documentation beyond what's already provided
        - Base your decision on the financial data provided, not on missing documentation

        Provide a detailed analysis in the following JSON format:
        {{
            "risk_assessment": {{
                "overall_risk": "low/medium/high",
                "risk_factors": ["list", "of", "specific", "risk", "factors"],
                "risk_score": 0.0 to 1.0
            }},
            "financial_analysis": {{
                "dti_analysis": "detailed analysis of DTI",
                "ltv_analysis": "detailed analysis of LTV",
                "income_analysis": "detailed analysis of income stability",
                "credit_analysis": "detailed analysis of credit profile"
            }},
            "property_analysis": {{
                "location_risk": "analysis of property location",
                "property_type_risk": "analysis of property type",
                "value_analysis": "analysis of property value"
            }},
            "required_documents": ["list", "of", "required", "documents"],
            "recommendations": ["list", "of", "specific", "recommendations"],
            "approval_decision": {{
                "approved": true/false,
                "confidence": 0.0 to 1.0,
                "explanation": "detailed explanation of decision"
            }}
        }}
        """
    
    def _parse_analysis(self, analysis: str) -> Dict:
        """Parse the Gemini response into structured format"""
        try:
            # Convert the text response to a dictionary
            parsed = json.loads(analysis)
            logger.info("Successfully parsed JSON analysis")
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse analysis: {str(e)}")
            # If parsing fails, return a default structure
            return {
                "risk_assessment": {
                    "overall_risk": "high",
                    "risk_factors": ["Unable to parse analysis"],
                    "risk_score": 1.0
                },
                "approval_decision": {
                    "approved": False,
                    "confidence": 0.0,
                    "explanation": "Error in analysis parsing"
                }
            }
    
    def _calculate_dti(self, application: LoanApplication) -> float:
        """Calculate Debt-to-Income ratio"""
        total_monthly_debt = application.monthly_debt
        total_monthly_income = application.annual_income / 12
        return total_monthly_debt / total_monthly_income if total_monthly_income > 0 else float('inf')
    
    def _calculate_ltv(self, application: LoanApplication) -> float:
        """Calculate Loan-to-Value ratio"""
        return application.loan_amount / application.property_value
    
    def _calculate_reserves(self, application: LoanApplication) -> float:
        """Calculate reserves ratio"""
        monthly_payment = self._calculate_monthly_payment(application)
        total_reserves = application.annual_income / 12 * 3
        return total_reserves / monthly_payment if monthly_payment > 0 else 0
    
    def _calculate_monthly_payment(self, application: LoanApplication) -> float:
        """Calculate monthly mortgage payment"""
        loan_amount = application.loan_amount
        interest_rate = application.interest_rate
        loan_term = application.loan_term_years
        
        monthly_rate = interest_rate / 12
        num_payments = loan_term * 12
        pi = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
        
        monthly_taxes = 0  # Not available in flat model
        monthly_insurance = 0  # Not available in flat model
        
        return pi + monthly_taxes + monthly_insurance
    
    def learn_from_decision(self, application: LoanApplication, decision: ValidationResult) -> None:
        """Store decision in database for future learning"""
        logger.info(f"Learning from decision for application ID: {application.id}")
        db = SessionLocal()
        try:
            # Create vector embedding for similarity search
            embedding = self._create_embedding(application)
            
            # Create new decision history record
            history = DecisionHistory(
                application_id=application.id,
                credit_score=application.credit_score,
                annual_income=application.annual_income,
                loan_amount=application.loan_amount,
                property_value=application.property_value,
                dti_ratio=self._calculate_dti(application),
                ltv_ratio=self._calculate_ltv(application),
                is_approved=1 if decision.is_approved else 0,
                risk_score=decision.risk_score,
                risk_factors=decision.risk_flags,
                recommendations=decision.recommendations,
                property_type=application.property_type,
                employment_years=application.years_employed,
                down_payment=application.down_payment,
                embedding=embedding
            )
            
            db.add(history)
            db.commit()
            logger.info("Successfully stored decision in database")
        finally:
            db.close()
    
    def get_similar_cases(self, application: LoanApplication, limit: int = 5) -> List[DecisionHistory]:
        """Find similar past cases using vector similarity search"""
        logger.info(f"Finding similar cases for application ID: {application.id}")
        db = SessionLocal()
        try:
            # Get all cases
            all_cases = db.query(DecisionHistory).all()
            logger.info(f"Retrieved {len(all_cases)} total cases from database")
            
            if not all_cases:
                return []
            
            # Create embedding for current application
            current_embedding = self._create_embedding(application)
            
            # Calculate similarities
            similarities = []
            for case in all_cases:
                similarity = cosine_similarity(
                    [current_embedding],
                    [case.embedding]
                )[0][0]
                similarities.append((case, similarity))
            
            # Sort by similarity and return top matches
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_cases = [case for case, _ in similarities[:limit]]
            logger.info(f"Found {len(top_cases)} similar cases")
            return top_cases
        finally:
            db.close()
    
    def _create_embedding(self, application: LoanApplication) -> List[float]:
        """Create a vector embedding for similarity search"""
        # Normalize and combine key features
        features = [
            application.credit_score / 850,  # Normalize credit score
            application.annual_income / 1000000,  # Normalize income
            application.loan_amount / 1000000,  # Normalize loan amount
            self._calculate_dti(application),  # DTI ratio
            self._calculate_ltv(application),  # LTV ratio
            application.years_employed / 40,  # Normalize employment years
            application.down_payment / application.property_value  # Down payment ratio
        ]
        return features

    def suggest_improvements_with_llm(self, application, risk_flags, guideline_context):
        """
        Use the LLM to generate personalized improvement recommendations based on failed rules and guideline context.
        """
        prompt = f"""
        The following loan application was rejected due to these risk flags: {risk_flags}.
        Here is the applicant's summary:
        - Name: {application.borrower_name}
        - Credit Score: {application.credit_score}
        - Annual Income: {application.annual_income}
        - Loan Amount: {application.loan_amount}
        - Property Value: {application.property_value}
        - Down Payment: {application.down_payment}
        - DTI: {application.monthly_debt / (application.annual_income / 12):.2f}
        - LTV: {application.loan_amount / application.property_value:.2f}

        For each failed rule, here are relevant guidelines:
        {json.dumps(guideline_context, indent=2)}

        Please provide actionable, specific recommendations for the applicant to improve their chances of approval, referencing the guidelines where appropriate. Respond with a JSON list of recommendations.
        """
        response = self.llm_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert mortgage underwriter."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        # Parse and return the recommendations
        return json.loads(response.choices[0].message.content) 