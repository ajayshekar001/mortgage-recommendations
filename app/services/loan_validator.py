from typing import List, Dict, Tuple
from app.models.loan_application import LoanApplication, ValidationResult
from app.agents.loan_agent import LoanAgent
from app.services.knowledge_service import KnowledgeService
from app.db.session import SessionLocal
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoanValidator:
    # Underwriting thresholds
    MAX_DTI_RATIO = 0.43  # 43% maximum DTI ratio
    MAX_LTV_RATIO = 0.97  # 97% maximum LTV ratio
    MIN_CREDIT_SCORE = 620  # Minimum credit score for conventional loans
    MIN_DOWN_PAYMENT = 0.03  # 3% minimum down payment for conventional loans
    
    # Risk thresholds
    DTI_RISK_THRESHOLDS = {
        'low': 0.36,    # Below 36% - Low risk
        'medium': 0.43, # 36-43% - Medium risk
        'high': 0.50    # Above 43% - High risk
    }
    
    LTV_RISK_THRESHOLDS = {
        'low': 0.80,    # Below 80% - Low risk
        'medium': 0.90, # 80-90% - Medium risk
        'high': 0.97    # Above 90% - High risk
    }
    
    CREDIT_SCORE_THRESHOLDS = {
        'excellent': 760,
        'good': 700,
        'fair': 660,
        'poor': 620
    }
    
    # Risk weights for different risk factors
    risk_weights = {
        'high_dti': 0.3,
        'high_ltv': 0.3,
        'low_credit': 0.2,
        'low_down_payment': 0.2
    }
    
    # Risk reduction factors
    risk_reduction_factors = {
        'strong_income': 0.1,
        'low_ltv': 0.1,
        'high_reserves': 0.1
    }

    def __init__(self):
        self.agent = LoanAgent()
        self.knowledge_service = KnowledgeService()
        logger.info("Initialized LoanValidator with LoanAgent and KnowledgeService")

    def calculate_dti(self, application: LoanApplication) -> float:
        """Calculate Debt-to-Income ratio"""
        total_monthly_debt = application.monthly_debt
        total_monthly_income = application.annual_income / 12
        return total_monthly_debt / total_monthly_income if total_monthly_income > 0 else float('inf')

    def calculate_ltv(self, application: LoanApplication) -> float:
        """Calculate Loan-to-Value ratio"""
        return application.loan_amount / application.property_value

    def calculate_reserves_ratio(self, application: LoanApplication) -> float:
        """Calculate reserves ratio (total liquid assets / monthly mortgage payment)"""
        monthly_payment = self.calculate_monthly_payment(application)
        total_reserves = application.annual_income / 12 * 3
        return total_reserves / monthly_payment if monthly_payment > 0 else 0

    def calculate_monthly_payment(self, application: LoanApplication) -> float:
        """Calculate monthly mortgage payment including PITI"""
        loan_amount = application.loan_amount
        interest_rate = application.interest_rate
        loan_term = application.loan_term_years
        
        monthly_rate = interest_rate / 12
        num_payments = loan_term * 12
        pi = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
        
        monthly_taxes = 0  # Not available in flat model
        monthly_insurance = 0  # Not available in flat model
        
        return pi + monthly_taxes + monthly_insurance

    def get_dti_risk_level(self, dti: float) -> str:
        """Determine DTI risk level"""
        if dti <= self.DTI_RISK_THRESHOLDS['low']:
            return 'low'
        elif dti <= self.DTI_RISK_THRESHOLDS['medium']:
            return 'medium'
        else:
            return 'high'

    def get_ltv_risk_level(self, ltv: float) -> str:
        """Determine LTV risk level"""
        if ltv <= self.LTV_RISK_THRESHOLDS['low']:
            return 'low'
        elif ltv <= self.LTV_RISK_THRESHOLDS['medium']:
            return 'medium'
        else:
            return 'high'

    def get_credit_score_risk_level(self, credit_score: int) -> str:
        """Determine credit score risk level"""
        if credit_score >= self.CREDIT_SCORE_THRESHOLDS['excellent']:
            return 'excellent'
        elif credit_score >= self.CREDIT_SCORE_THRESHOLDS['good']:
            return 'good'
        elif credit_score >= self.CREDIT_SCORE_THRESHOLDS['fair']:
            return 'fair'
        else:
            return 'poor'

    def calculate_risk_score(self, application: LoanApplication, risk_flags: List[str]) -> float:
        """Calculate comprehensive risk score based on multiple factors"""
        logger.info(f"Calculating risk score for application ID: {application.id}")
        base_risk = 0.0
        
        # Calculate base risk from flags
        for flag in risk_flags:
            if flag in self.risk_weights:
                base_risk += self.risk_weights[flag]
        logger.info(f"Base risk from flags: {base_risk}")
        
        # Calculate DTI risk
        dti = self.calculate_dti(application)
        dti_risk_level = self.get_dti_risk_level(dti)
        logger.info(f"DTI ratio: {dti:.2%}, Risk level: {dti_risk_level}")
        if dti_risk_level == 'high':
            base_risk += 0.25
        elif dti_risk_level == 'medium':
            base_risk += 0.15
        
        # Calculate LTV risk
        ltv = self.calculate_ltv(application)
        ltv_risk_level = self.get_ltv_risk_level(ltv)
        logger.info(f"LTV ratio: {ltv:.2%}, Risk level: {ltv_risk_level}")
        if ltv_risk_level == 'high':
            base_risk += 0.25
        elif ltv_risk_level == 'medium':
            base_risk += 0.15
        
        # Calculate credit score risk
        if application.credit_score:
            credit_risk_level = self.get_credit_score_risk_level(application.credit_score)
            logger.info(f"Credit score: {application.credit_score}, Risk level: {credit_risk_level}")
            if credit_risk_level == 'poor':
                base_risk += 0.20
            elif credit_risk_level == 'fair':
                base_risk += 0.10
        
        # Apply risk reduction factors
        risk_reduction = 0.0
        
        # Strong income (if DTI is low)
        if dti_risk_level == 'low':
            risk_reduction += self.risk_reduction_factors['strong_income']
        
        # Low LTV
        if ltv_risk_level == 'low':
            risk_reduction += self.risk_reduction_factors['low_ltv']
        
        # High reserves
        reserves_ratio = self.calculate_reserves_ratio(application)
        logger.info(f"Reserves ratio: {reserves_ratio:.2f}")
        if reserves_ratio >= 6:  # 6 months of reserves
            risk_reduction += self.risk_reduction_factors['high_reserves']
        
        # Apply risk reduction
        final_risk = max(0.0, base_risk - risk_reduction)
        logger.info(f"Final risk score: {final_risk:.2f}")
        
        return min(final_risk, 1.0)

    def validate_documents(self, application: LoanApplication) -> List[str]:
        """Check for missing required documents based on validation results"""
        # Base required documents for all applications
        required_docs = {
            # 'ID': 'Government-issued photo ID',
            # 'CreditReport': 'Credit report authorization'
        }
        
        # Check DTI ratio
        dti_ratio = self.calculate_dti(application)
        if dti_ratio > self.DTI_RISK_THRESHOLDS['low']:
            required_docs.update({
                'W2': 'W-2 forms for the last 2 years',
                'PayStub': 'Most recent pay stubs covering 30 days',
                'TaxReturn': 'Tax returns for the last 2 years'
            })
        
        # Check LTV ratio
        ltv_ratio = self.calculate_ltv(application)
        if ltv_ratio > self.LTV_RISK_THRESHOLDS['low']:
            required_docs.update({
                'BankStatement': 'Bank statements for the last 2 months',
                'AssetStatement': 'Statements for all assets (checking, savings, investments)'
            })
        
        # Check credit score
        if application.credit_score and application.credit_score < self.CREDIT_SCORE_THRESHOLDS['good']:
            required_docs.update({
                'EmploymentVerification': 'Employment verification letter',
                'BankStatement': 'Bank statements for the last 2 months'
            })
        
        # Check down payment
        down_payment_ratio = application.down_payment / application.property_value
        if down_payment_ratio < 0.20:  # Less than 20% down payment
            required_docs.update({
                'PurchaseAgreement': 'Signed purchase agreement',
                'InsuranceQuote': 'Homeowners insurance quote'
            })
        
        # Check provided documents
        provided_docs = {doc.document_type for doc in application.documents}
        missing_docs = required_docs.keys() - provided_docs
        
        return [f"Missing {doc_type}: {description}" for doc_type, description in required_docs.items() if doc_type in missing_docs]

    def get_llm_validation(self, application: LoanApplication) -> Dict:
        """Get dynamic validation from LLM based on application context"""
        prompt = f"""
        Analyze this loan application and provide validation insights:
        
        Borrower Profile:
        - Credit Score: {application.credit_score}
        - Annual Income: ${application.annual_income:,.2f}
        - Employment: {application.employer_name} ({application.years_employed} years)
        
        Loan Details:
        - Amount: ${application.loan_amount:,.2f}
        - Interest Rate: {application.interest_rate:.2%}
        - Term: {application.loan_term_years} years
        
        Property:
        - Value: ${application.property_value:,.2f}
        - Down Payment: ${application.down_payment:,.2f}
        - Type: {application.property_type}
        
        Financial Metrics:
        - DTI Ratio: {self.calculate_dti(application):.2%}
        - LTV Ratio: {self.calculate_ltv(application):.2%}
        - Reserves Ratio: {self.calculate_reserves_ratio(application):.2f}
        
        Provide a JSON response with:
        1. risk_assessment: Overall risk level (low/medium/high)
        2. risk_factors: List of specific risk factors identified
        3. required_documents: List of documents needed based on risk factors
        4. recommendations: List of specific recommendations
        5. approval_decision: Boolean indicating if application should be approved
        6. explanation: Detailed explanation of the decision
        """
        
        response = self.llm_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert mortgage underwriter with deep knowledge of lending guidelines and risk assessment. Provide detailed, contextual analysis of loan applications."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content

    def check_hard_rules(self, application: LoanApplication) -> List[str]:
        """Check hard rules using the knowledge graph or rule engine."""
        risk_flags = []
        dti_ratio = self.calculate_dti(application)
        ltv_ratio = self.calculate_ltv(application)
        if dti_ratio > self.MAX_DTI_RATIO:
            risk_flags.append("high_dti")
        if ltv_ratio > self.MAX_LTV_RATIO:
            risk_flags.append("high_ltv")
        if application.credit_score < self.MIN_CREDIT_SCORE:
            risk_flags.append("low_credit")
        down_payment_ratio = application.down_payment / application.property_value
        if down_payment_ratio < self.MIN_DOWN_PAYMENT:
            risk_flags.append("low_down_payment")
        return risk_flags

    def validate_application(self, application: LoanApplication) -> ValidationResult:
        logger.info(f"Starting validation for application ID: {application.id}")

        # 1. Hard rule checks
        risk_flags = self.check_hard_rules(application)
        if risk_flags:
            logger.info("Hard thresholds violated - rejecting application")
            # Fetch guideline context for failed rules
            guideline_context = self.knowledge_service.get_context_for_flags(risk_flags, application)
            logger.info(f"Guideline context for failed rules: {guideline_context}")

            # NEW: Get LLM-powered recommendations
            logger.info("Calling LLM for improvement recommendations...")
            llm_response = self.agent.suggest_improvements_with_llm(application, risk_flags, guideline_context)
            logger.info(f"LLM recommendations: {llm_response}")
            
            # Parse LLM recommendations properly
            llm_recommendations = []
            if isinstance(llm_response, dict) and 'recommendations' in llm_response:
                for rec in llm_response['recommendations']:
                    if isinstance(rec, dict):
                        # Extract detailed recommendation
                        if 'detail' in rec:
                            llm_recommendations.append(rec['detail'])
                        elif 'title' in rec:
                            llm_recommendations.append(rec['title'])
                    elif isinstance(rec, str):
                        llm_recommendations.append(rec)
            elif isinstance(llm_response, list):
                llm_recommendations = llm_response
            logger.info(f"Parsed LLM recommendations: {llm_recommendations}")

            explanation = self.generate_explanation(
                risk_flags, self.calculate_dti(application), self.calculate_ltv(application), application
            )
            recommendations = self.generate_recommendations(application, risk_flags)
            if llm_recommendations:
                recommendations.extend(llm_recommendations)
            risk_score = self.calculate_risk_score(application, risk_flags)
            logger.info(f"Final recommendations: {recommendations}")
            return ValidationResult(
                application_id=application.id,
                is_approved=False,
                risk_score=risk_score,
                risk_flags=risk_flags,
                recommendations=recommendations,
                dti_ratio=self.calculate_dti(application),
                ltv_ratio=self.calculate_ltv(application),
                explanation=explanation
            )

        # 2. Gather context from knowledge graph (to be implemented next)
        context = None  # Placeholder for knowledge graph context

        # 3. LLM analysis (to be implemented next)
        llm_result = None  # Placeholder for LLM result
        # For now, fallback to previous knowledge service logic
        analysis = self.knowledge_service.analyze_with_guidelines(application)
        logger.info("Received analysis from knowledge service")
        logger.debug(f"Analysis: {analysis}")
        risk_assessment = analysis["overall_analysis"]["risk_assessment"]
        approval_decision = analysis["overall_analysis"]["approval_decision"]
        logger.info(f"Knowledge service risk assessment: {risk_assessment}")
        logger.info(f"Knowledge service approval decision: {approval_decision}")
        result = ValidationResult(
            application_id=application.id,
            is_approved=approval_decision["approved"],
            risk_score=risk_assessment["risk_score"],
            risk_flags=risk_assessment["risk_factors"],
            recommendations=self._extract_recommendations(analysis),
            dti_ratio=self.calculate_dti(application),
            ltv_ratio=self.calculate_ltv(application),
            explanation=approval_decision["explanation"]
        )
        logger.info(f"Created validation result: {result}")
        return result
    
    def _extract_recommendations(self, analysis: Dict) -> List[str]:
        """Extract recommendations from guideline applications"""
        logger.info("Extracting recommendations from analysis")
        recommendations = set()
        
        # Add recommendations from guideline applications
        for app in analysis.get("guideline_applications", []):
            if not app["is_applicable"]:
                recommendations.add(app["impact"])
        
        logger.info(f"Extracted {len(recommendations)} recommendations")
        return list(recommendations)

    def calculate_risk_score_from_llm(self, llm_validation: Dict) -> float:
        """Calculate risk score based on LLM assessment"""
        risk_level = llm_validation.get('risk_assessment', 'medium')
        risk_factors = llm_validation.get('risk_factors', [])
        
        # Base risk score from risk level
        base_risk = {
            'low': 0.2,
            'medium': 0.5,
            'high': 0.8
        }.get(risk_level, 0.5)
        
        # Adjust based on number of risk factors
        factor_adjustment = len(risk_factors) * 0.1
        final_risk = min(base_risk + factor_adjustment, 1.0)
        
        return final_risk

    def generate_recommendations(self, application: LoanApplication, risk_flags: List[str]) -> List[str]:
        """Generate recommendations based on risk flags"""
        recommendations = []
        
        if 'high_dti' in risk_flags:
            recommendations.append("Consider increasing down payment to reduce monthly payments")
            recommendations.append("Look for opportunities to reduce existing debt")
        
        if 'high_ltv' in risk_flags:
            recommendations.append("Consider increasing down payment to improve LTV ratio")
        
        if 'low_credit' in risk_flags:
            recommendations.append("Consider improving credit score before proceeding")
        
        if 'missing_docs' in risk_flags:
            recommendations.append("Please provide the following required documentation:")
            missing_docs = self.validate_documents(application)
            recommendations.extend([f"- {doc}" for doc in missing_docs])
        
        if 'low_down_payment' in risk_flags:
            recommendations.append(f"Increase down payment to meet minimum requirement of {self.MIN_DOWN_PAYMENT:.1%}")
        
        return recommendations

    def generate_explanation(self, risk_flags: List[str], dti_ratio: float, ltv_ratio: float, application: LoanApplication) -> str:
        """Generate human-readable explanation of validation results"""
        if not risk_flags:
            return "Application meets all underwriting criteria"
        
        explanations = []
        if 'high_dti' in risk_flags:
            explanations.append(f"DTI ratio of {dti_ratio:.1%} exceeds maximum allowed {self.MAX_DTI_RATIO:.1%}")
        if 'high_ltv' in risk_flags:
            explanations.append(f"LTV ratio of {ltv_ratio:.1%} exceeds maximum allowed {self.MAX_LTV_RATIO:.1%}")
        if 'low_credit' in risk_flags:
            explanations.append(f"Credit score below minimum required {self.MIN_CREDIT_SCORE}")
        if 'missing_docs' in risk_flags:
            missing_docs = self.validate_documents(application)
            explanations.append("Missing required documentation")
            explanations.extend([f"- {doc}" for doc in missing_docs])
        if 'low_down_payment' in risk_flags:
            explanations.append(f"Down payment below minimum required {self.MIN_DOWN_PAYMENT:.1%}")
        
        return "Application requires attention: " + "; ".join(explanations) 