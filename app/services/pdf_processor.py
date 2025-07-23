import pdfplumber
from typing import Dict, List, Optional
import re
from datetime import datetime
import json

class PDFProcessor:
    def __init__(self):
        self.w2_patterns = {
            'wages': r'Wages, tips, other comp\.\s*(\d+,?\d*\.?\d*)',
            'federal_tax': r'Federal income tax withheld\s*(\d+,?\d*\.?\d*)',
            'ssn': r'SSN\s*(\d{3}-\d{2}-\d{4})',
            'employer': r'Employer\'s name, address, and ZIP code\s*(.*?)(?=\n)'
        }
        
        self.bank_statement_patterns = {
            'account_number': r'Account Number:\s*(\d+)',
            'balance': r'Ending Balance\s*\$?(\d+,?\d*\.?\d*)',
            'transactions': r'(\d{2}/\d{2}/\d{4})\s+(.*?)\s+\$?(\d+,?\d*\.?\d*)'
        }

    def extract_w2_data(self, pdf_path: str) -> Dict:
        """Extract data from W-2 form"""
        data = {}
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text()
                
                # Extract data using patterns
                for field, pattern in self.w2_patterns.items():
                    match = re.search(pattern, text)
                    if match:
                        data[field] = match.group(1).strip()
                
                # Convert wages to float
                if 'wages' in data:
                    data['wages'] = float(data['wages'].replace(',', ''))
                
                return data
        except Exception as e:
            print(f"Error processing W-2: {str(e)}")
            return {}

    def extract_bank_statement_data(self, pdf_path: str) -> Dict:
        """Extract data from bank statement"""
        data = {
            'account_number': None,
            'balance': None,
            'transactions': []
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text()
                
                # Extract account number
                account_match = re.search(self.bank_statement_patterns['account_number'], text)
                if account_match:
                    data['account_number'] = account_match.group(1)
                
                # Extract balance
                balance_match = re.search(self.bank_statement_patterns['balance'], text)
                if balance_match:
                    data['balance'] = float(balance_match.group(1).replace(',', ''))
                
                # Extract transactions
                transactions = re.finditer(self.bank_statement_patterns['transactions'], text)
                for match in transactions:
                    date_str, description, amount = match.groups()
                    try:
                        date = datetime.strptime(date_str, '%m/%d/%Y')
                        amount = float(amount.replace(',', ''))
                        data['transactions'].append({
                            'date': date.isoformat(),
                            'description': description.strip(),
                            'amount': amount
                        })
                    except ValueError:
                        continue
                
                return data
        except Exception as e:
            print(f"Error processing bank statement: {str(e)}")
            return {}

    def extract_1003_data(self, pdf_path: str) -> Dict:
        """Extract data from URLA (Form 1003)"""
        # TODO: Implement 1003 form extraction
        # This would require more complex pattern matching and form field recognition
        return {}

    def process_document(self, pdf_path: str, document_type: str) -> Dict:
        """Process a document based on its type"""
        processors = {
            'W2': self.extract_w2_data,
            'BankStatement': self.extract_bank_statement_data,
            'Form1003': self.extract_1003_data
        }
        
        if document_type not in processors:
            raise ValueError(f"Unsupported document type: {document_type}")
        
        return processors[document_type](pdf_path)

    def extract_to_mismo(self, extracted_data: Dict, document_type: str) -> str:
        """Convert extracted data to MISMO 3.4 XML format"""
        # TODO: Implement MISMO XML conversion
        # This would require mapping the extracted data to MISMO 3.4 schema
        return json.dumps(extracted_data)  # Temporary JSON output 