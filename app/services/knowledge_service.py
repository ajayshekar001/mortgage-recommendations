from typing import List, Dict, Optional
import google.generativeai as genai
from app.core.config import settings
from app.models.knowledge_graph import GuidelineNode, GuidelineApplication
from app.models.loan_application import LoanApplication
from app.db.session import SessionLocal
from datetime import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeService:
    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        logger.info("Initialized KnowledgeService with Gemini model")
    
    def analyze_with_guidelines(self, application: LoanApplication) -> Dict:
        """Analyze loan application using knowledge graph and chain-of-thought reasoning"""
        logger.info(f"Starting analysis for application ID: {application.id}")
        db = SessionLocal()
        try:
            # Get relevant guidelines
            relevant_guidelines = self._get_relevant_guidelines(application, db)
            logger.info(f"Found {len(relevant_guidelines)} relevant guidelines")
            
            # Create chain-of-thought analysis
            analysis = self._create_chain_of_thought(application, relevant_guidelines)
            logger.info("Generated chain-of-thought analysis")
            
            # Store guideline applications
            self._store_guideline_applications(application, analysis, db)
            logger.info("Stored guideline applications in database")
            
            return analysis
        finally:
            db.close()
    
    def _get_relevant_guidelines(self, application: LoanApplication, db) -> List[GuidelineNode]:
        """Find relevant guidelines using semantic search"""
        logger.info("Finding relevant guidelines using semantic search")
        # Create embedding for current application
        application_embedding = self._create_application_embedding(application)
        
        # Get all guidelines
        all_guidelines = db.query(GuidelineNode).all()
        logger.info(f"Retrieved {len(all_guidelines)} total guidelines from database")
        
        # Calculate similarities
        similarities = []
        for guideline in all_guidelines:
            similarity = cosine_similarity(
                [application_embedding],
                [guideline.embedding]
            )[0][0]
            similarities.append((guideline, similarity))
        
        # Sort by similarity and return top matches
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_guidelines = [guideline for guideline, _ in similarities[:10]]
        logger.info(f"Selected top {len(top_guidelines)} guidelines by similarity")
        return top_guidelines
    
    def _create_chain_of_thought(self, application: LoanApplication, guidelines: List[GuidelineNode]) -> Dict:
        """Create chain-of-thought analysis using guidelines"""
        logger.info("Creating chain-of-thought analysis")
        # Create prompt for chain-of-thought reasoning
        prompt = self._create_chain_of_thought_prompt(application, guidelines)
        logger.debug(f"Generated prompt: {prompt}")
        
        # Get analysis from Gemini
        response = self.model.generate_content(prompt)
        analysis = response.text
        logger.info("Received response from Gemini model")
        logger.debug(f"Raw analysis: {analysis}")
        
        # Parse the analysis
        parsed_analysis = self._parse_chain_of_thought(analysis)
        logger.info("Successfully parsed analysis")
        return parsed_analysis
    
    def _create_chain_of_thought_prompt(self, application: LoanApplication, guidelines: List[GuidelineNode]) -> str:
        """Create a detailed prompt for chain-of-thought reasoning"""
        guidelines_text = "\n\n".join([
            f"Guideline {i+1}: {guideline.title}\n"
            f"Category: {guideline.category}\n"
            f"Content: {guideline.content}\n"
            f"Source: {guideline.source} {guideline.version}\n"
            f"Metadata: {json.dumps(guideline.guideline_metadata, indent=2)}"
            for i, guideline in enumerate(guidelines)
        ])
        
        return f"""
        You are an expert mortgage underwriter. Analyze this loan application using the following guidelines.
        Show your chain of thought for each guideline application, considering all relevant factors and their interactions.

        APPLICATION DETAILS:
        Borrower Profile:
        - Borrower Name: {application.borrower_name}
        - Credit Score: {application.credit_score}
        - Annual Income: ${application.annual_income:,.2f}
        - Employment: {application.employer_name} ({application.years_employed} years)
        - Monthly Debts: ${application.monthly_debt:,.2f}
        - Employment Type: {application.employment_status}

        Loan Details:
        - Amount: ${application.loan_amount:,.2f}
        - Interest Rate: {application.interest_rate:.2%}
        - Term: {application.loan_term_years} years
        - Property Value: ${application.property_value:,.2f}
        - Down Payment: ${application.down_payment:,.2f}

        Financial Metrics:
        - DTI Ratio: {self._calculate_dti(application):.2%}
        - LTV Ratio: {self._calculate_ltv(application):.2%}

        RELEVANT GUIDELINES:
        {guidelines_text}

        ANALYSIS INSTRUCTIONS:
        1. For each guideline:
           - Explain how it applies to this specific application
           - Consider any exceptions or compensating factors
           - Evaluate the impact on the overall risk assessment
           - Provide confidence level in your assessment

        2. For the overall analysis:
           - Consider interactions between different guidelines
           - Evaluate compensating factors across multiple areas
           - Assess the overall risk profile
           - Make a final approval decision with detailed explanation

        IMPORTANT CONSTRAINTS:
        - Focus ONLY on core financial metrics: DTI ratio, LTV ratio, credit score, income stability, and employment history
        - DO NOT include document type validations like property_type, market_conditions, asset_documentation, or employment verification
        - DO NOT require additional documentation beyond what's already provided
        - Base your decision on the financial data provided, not on missing documentation

        IMPORTANT: You must respond with a valid JSON object in the following format:
        {{
            "guideline_applications": [
                {{
                    "guideline_id": "id of the guideline",
                    "is_applicable": true/false,
                    "reasoning": "step-by-step reasoning including:
                                 - How the guideline applies
                                 - Any exceptions considered
                                 - Compensating factors evaluated
                                 - Impact on risk assessment",
                    "impact": "specific impact on the decision",
                    "confidence": 0.0 to 1.0,
                    "compensating_factors": ["list", "of", "compensating", "factors"],
                    "risk_implications": "how this affects overall risk"
                }}
            ],
            "overall_analysis": {{
                "risk_assessment": {{
                    "overall_risk": "low/medium/high",
                    "risk_factors": ["list", "of", "risk", "factors"],
                    "risk_score": 0.0 to 1.0,
                    "compensating_factors": ["list", "of", "compensating", "factors"],
                    "risk_mitigation": "how risks are mitigated"
                }},
                "approval_decision": {{
                    "approved": true/false,
                    "confidence": 0.0 to 1.0,
                    "explanation": "detailed explanation of decision including:
                                  - Key factors in the decision
                                  - How guidelines were applied
                                  - Compensating factors considered
                                  - Risk mitigation strategies",
                    "conditions": ["list", "of", "approval", "conditions"],
                    "recommendations": ["list", "of", "recommendations"]
                }},
                "key_factors": {{
                    "primary_factors": ["list", "of", "primary", "factors"],
                    "secondary_factors": ["list", "of", "secondary", "factors"],
                    "mitigating_factors": ["list", "of", "mitigating", "factors"],
                    "risk_factors": ["list", "of", "risk", "factors"]
                }}
            }}
        }}

        Do not include any text before or after the JSON object. The response must be a valid JSON object that can be parsed.
        """
    
    def _parse_chain_of_thought(self, analysis: str) -> Dict:
        """Parse the chain-of-thought analysis"""
        try:
            # Strip triple backticks and optional 'json' label
            cleaned = analysis.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[len('```json'):].strip()
            if cleaned.startswith('```'):
                cleaned = cleaned[len('```'):].strip()
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3].strip()
            parsed = json.loads(cleaned)
            logger.info("Successfully parsed JSON analysis")
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse analysis: {str(e)}")
            logger.error(f"Raw analysis: {analysis}")
            # Return a default response with error information
            return {
                "guideline_applications": [],
                "overall_analysis": {
                    "risk_assessment": {
                        "overall_risk": "high",
                        "risk_factors": ["Error in analysis parsing"],
                        "risk_score": 1.0,
                        "compensating_factors": [],
                        "risk_mitigation": "Error in analysis parsing"
                    },
                    "approval_decision": {
                        "approved": False,
                        "confidence": 0.0,
                        "explanation": "Error in analysis parsing",
                        "conditions": [],
                        "recommendations": []
                    },
                    "key_factors": {
                        "primary_factors": [],
                        "secondary_factors": [],
                        "mitigating_factors": [],
                        "risk_factors": ["Error in analysis parsing"]
                    }
                }
            }
    
    def _store_guideline_applications(self, application: LoanApplication, analysis: Dict, db) -> None:
        """Store guideline applications in the database"""
        for app in analysis.get("guideline_applications", []):
            guideline_app = GuidelineApplication(
                application_id=application.id,
                guideline_id=app["guideline_id"],
                is_applicable=1 if app["is_applicable"] else 0,
                reasoning=app["reasoning"],
                impact=app["impact"],
                confidence=app["confidence"]
            )
            db.add(guideline_app)
        db.commit()
    
    def _create_application_embedding(self, application: LoanApplication) -> List[float]:
        """Create embedding for semantic search"""
        features = [
            application.credit_score / 850,
            application.annual_income / 1000000,
            application.loan_amount / 1000000,
            self._calculate_dti(application),
            self._calculate_ltv(application),
            application.years_employed / 40,
            application.down_payment / application.property_value
        ]
        return features
    
    def _calculate_dti(self, application: LoanApplication) -> float:
        """Calculate Debt-to-Income ratio"""
        total_monthly_debt = application.monthly_debt
        total_monthly_income = application.annual_income / 12
        return total_monthly_debt / total_monthly_income if total_monthly_income > 0 else float('inf')
    
    def _calculate_ltv(self, application: LoanApplication) -> float:
        """Calculate Loan-to-Value ratio"""
        return application.loan_amount / application.property_value

    def get_context_for_flags(self, risk_flags: list, application) -> dict:
        """
        Given a list of risk flags and the application, fetch relevant guidelines or context from the knowledge graph.
        Returns a dictionary mapping each flag to a list of relevant guideline summaries.
        """
        context = {}
        db = SessionLocal()
        try:
            for flag in risk_flags:
                # Example: map flag to a category or keyword
                if flag == "high_dti":
                    guidelines = db.query(GuidelineNode).filter(GuidelineNode.category.ilike("%DTI%") | GuidelineNode.content.ilike("%debt%") ).limit(5).all()
                elif flag == "high_ltv":
                    guidelines = db.query(GuidelineNode).filter(GuidelineNode.category.ilike("%LTV%") | GuidelineNode.content.ilike("%loan-to-value%") ).limit(5).all()
                elif flag == "low_credit":
                    guidelines = db.query(GuidelineNode).filter(GuidelineNode.category.ilike("%Credit%") | GuidelineNode.content.ilike("%credit score%") ).limit(5).all()
                elif flag == "low_down_payment":
                    guidelines = db.query(GuidelineNode).filter(GuidelineNode.content.ilike("%down payment%") ).limit(5).all()
                else:
                    guidelines = db.query(GuidelineNode).filter(GuidelineNode.content.ilike(f"%{flag}%")).limit(5).all()
                # Summarize guidelines for LLM/context
                context[flag] = [g.to_dict() for g in guidelines]
        finally:
            db.close()
        return context 