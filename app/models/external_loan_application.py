from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Address(BaseModel):
    address: str
    city: str
    state: str
    zip: str
    country: Optional[str] = "United States"

class Employment(BaseModel):
    employerName: str
    position: str
    startDate: str
    incomeMonthly: float
    selfEmployed: bool

class Income(BaseModel):
    base: float
    overtime: float
    bonuses: float
    otherIncome: float

class Asset(BaseModel):
    type: str
    institution: str
    amount: float

class Liability(BaseModel):
    type: str
    monthlyPayment: float
    unpaidBalance: float
    creditorName: str

class Borrower(BaseModel):
    firstName: str
    lastName: str
    ssn: str
    dob: str
    maritalStatus: str
    email: str
    phone: str
    creditScore: Optional[int] = 750
    residences: List[Address]
    employment: List[Employment]
    income: Income
    assets: List[Asset]
    liabilities: List[Liability]

class Loan(BaseModel):
    loanAmount: float
    loanPurpose: str
    propertyAddress: Address
    propertyValue: float
    occupancy: str
    loanType: str
    interestRate: float
    termMonths: int

class Declarations(BaseModel):
    bankruptcy: bool
    foreclosure: bool
    lawsuit: bool
    delinquentDebt: bool

class SubmissionMetadata(BaseModel):
    submittedAt: datetime
    submittedBy: str
    applicationId: str

class ExternalLoanApplication(BaseModel):
    loanApplication: dict  # Using dict to match the exact structure 