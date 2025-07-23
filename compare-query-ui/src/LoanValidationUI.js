import React, { useState } from "react";

export default function LoanValidationUI() {
  const [loanApplicationJson, setLoanApplicationJson] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Sample JSON for demonstration
  const sampleJson = JSON.stringify({
    "loanApplication": {
      "borrower": {
        "firstName": "Sarah",
        "lastName": "Johnson",
        "ssn": "456-78-9012",
        "dob": "1988-08-12",
        "maritalStatus": "married",
        "email": "sarah.johnson@email.com",
        "phone": "555-456-7890",
        "creditScore": 680,
        "residences": [
          {
            "address": "567 Maple Dr",
            "city": "Anytown",
            "state": "CA",
            "zip": "90210",
            "country": "United States"
          }
        ],
        "employment": [
          {
            "employerName": "Marketing Solutions",
            "position": "Marketing Manager",
            "startDate": "2021-03-01",
            "incomeMonthly": 6500,
            "selfEmployed": false
          }
        ],
        "income": {
          "base": 65000,
          "overtime": 3000,
          "bonuses": 8000,
          "otherIncome": 1000
        },
        "assets": [
          {
            "type": "checking",
            "institution": "Wells Fargo",
            "amount": 15000
          },
          {
            "type": "savings",
            "institution": "Wells Fargo",
            "amount": 8000
          }
        ],
        "liabilities": [
          {
            "type": "credit_card",
            "monthlyPayment": 450,
            "unpaidBalance": 8000,
            "creditorName": "American Express"
          },
          {
            "type": "car_loan",
            "monthlyPayment": 350,
            "unpaidBalance": 12000,
            "creditorName": "Toyota Financial"
          },
          {
            "type": "student_loan",
            "monthlyPayment": 200,
            "unpaidBalance": 15000,
            "creditorName": "Federal Student Aid"
          }
        ]
      },
      "loan": {
        "loanAmount": 380000,
        "loanPurpose": "purchase",
        "propertyAddress": {
          "address": "789 Pine Ave",
          "city": "Anytown",
          "state": "CA",
          "zip": "90210",
          "country": "United States"
        },
        "propertyValue": 475000,
        "occupancy": "primary",
        "loanType": "conventional",
        "interestRate": 5.2,
        "termMonths": 360
      },
      "declarations": {
        "bankruptcy": false,
        "foreclosure": false,
        "lawsuit": false,
        "delinquentDebt": false
      },
      "submissionMetadata": {
        "submittedAt": "2024-01-15T10:30:00Z",
        "submittedBy": "loan_officer_001",
        "applicationId": "app-medium-risk-001"
      }
    }
  }, null, 2);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      // Parse the JSON to validate it
      const parsedJson = JSON.parse(loanApplicationJson);
      
      const response = await fetch("http://localhost:8000/validate-application", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
        },
        body: JSON.stringify(parsedJson),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message.includes("JSON") ? "Invalid JSON format" : `Error: ${err.message}`);
    }
    setLoading(false);
  };

  const loadSampleData = () => {
    setLoanApplicationJson(sampleJson);
    setError(null);
    setResult(null);
  };

  const formatPercentage = (value) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const getApprovalStatusColor = (isApproved) => {
    return isApproved ? "#28a745" : "#dc3545";
  };

  const getRiskScoreColor = (riskScore) => {
    if (riskScore <= 0.3) return "#28a745"; // Green for low risk
    if (riskScore <= 0.6) return "#ffc107"; // Yellow for medium risk
    return "#dc3545"; // Red for high risk
  };

  return (
    <div style={{ 
      maxWidth: 1200, 
      margin: "0 auto", 
      padding: "20px",
      fontFamily: "Arial, sans-serif"
    }}>
      <div style={{
        backgroundColor: "white",
        padding: "30px",
        borderRadius: "8px",
        boxShadow: "0 2px 10px rgba(0,0,0,0.1)"
      }}>
        <h1 style={{ 
          color: "#333", 
          textAlign: "center",
          marginBottom: "30px",
          borderBottom: "3px solid #007bff",
          paddingBottom: "10px"
        }}>
          Loan Application Validator
        </h1>
        
        <div style={{ display: "flex", gap: "20px", marginBottom: "20px" }}>
          <button
            type="button"
            onClick={loadSampleData}
            style={{
              padding: "10px 20px",
              fontSize: "14px",
              background: "#6c757d",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer"
            }}
          >
            Load Sample Data
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "20px" }}>
            <label style={{ 
              display: "block", 
              marginBottom: "8px", 
              fontWeight: "bold",
              color: "#555"
            }}>
              Loan Application JSON:
            </label>
            <textarea
              rows={15}
              style={{ 
                width: "100%", 
                fontSize: "14px", 
                padding: "12px",
                border: "1px solid #ddd",
                borderRadius: "4px",
                fontFamily: "monospace",
                resize: "vertical"
              }}
              placeholder="Paste your loan application JSON here..."
              value={loanApplicationJson}
              onChange={(e) => setLoanApplicationJson(e.target.value)}
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading || !loanApplicationJson.trim()}
            style={{
              padding: "12px 30px",
              fontSize: "16px",
              background: loading ? "#6c757d" : "#007bff",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: loading ? "not-allowed" : "pointer",
              width: "100%"
            }}
          >
            {loading ? "Validating..." : "Validate Loan Application"}
          </button>
        </form>

        {error && (
          <div style={{
            marginTop: "20px",
            padding: "15px",
            backgroundColor: "#f8d7da",
            color: "#721c24",
            border: "1px solid #f5c6cb",
            borderRadius: "4px"
          }}>
            <strong>Error:</strong> {error}
          </div>
        )}

        {result && (
          <div style={{ marginTop: "30px" }}>
            <h2 style={{ 
              color: "#333",
              borderBottom: "2px solid #007bff",
              paddingBottom: "10px"
            }}>
              Validation Results
            </h2>
            
            <div style={{ 
              display: "grid", 
              gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
              gap: "20px",
              marginBottom: "20px"
            }}>
              <div style={{
                padding: "20px",
                backgroundColor: "#f8f9fa",
                border: "1px solid #dee2e6",
                borderRadius: "8px"
              }}>
                <h3 style={{ 
                  margin: "0 0 10px 0",
                  color: getApprovalStatusColor(result.is_approved)
                }}>
                  {result.is_approved ? "✅ APPROVED" : "❌ REJECTED"}
                </h3>
                <p style={{ margin: "5px 0", fontSize: "14px" }}>
                  <strong>Application ID:</strong> {result.application_id}
                </p>
              </div>

              <div style={{
                padding: "20px",
                backgroundColor: "#f8f9fa",
                border: "1px solid #dee2e6",
                borderRadius: "8px"
              }}>
                <h3 style={{ 
                  margin: "0 0 10px 0",
                  color: getRiskScoreColor(result.risk_score)
                }}>
                  Risk Score: {(result.risk_score * 100).toFixed(1)}%
                </h3>
                <p style={{ margin: "5px 0", fontSize: "14px" }}>
                  <strong>DTI Ratio:</strong> {formatPercentage(result.dti_ratio)}
                </p>
                <p style={{ margin: "5px 0", fontSize: "14px" }}>
                  <strong>LTV Ratio:</strong> {formatPercentage(result.ltv_ratio)}
                </p>
              </div>
            </div>

            {result.explanation && (
              <div style={{
                padding: "20px",
                backgroundColor: "#e7f3ff",
                border: "1px solid #b3d9ff",
                borderRadius: "8px",
                marginBottom: "20px"
              }}>
                <h3 style={{ margin: "0 0 10px 0", color: "#0056b3" }}>Explanation</h3>
                <p style={{ margin: 0, lineHeight: "1.6" }}>{result.explanation}</p>
              </div>
            )}

            {result.risk_flags && result.risk_flags.length > 0 && (
              <div style={{
                padding: "20px",
                backgroundColor: "#fff3cd",
                border: "1px solid #ffeaa7",
                borderRadius: "8px",
                marginBottom: "20px"
              }}>
                <h3 style={{ margin: "0 0 15px 0", color: "#856404" }}>⚠️ Risk Flags</h3>
                <ul style={{ margin: 0, paddingLeft: "20px" }}>
                  {result.risk_flags.map((flag, index) => (
                    <li key={index} style={{ marginBottom: "5px" }}>{flag}</li>
                  ))}
                </ul>
              </div>
            )}

            {result.recommendations && result.recommendations.length > 0 && (
              <div style={{
                padding: "20px",
                backgroundColor: "#d1ecf1",
                border: "1px solid #bee5eb",
                borderRadius: "8px"
              }}>
                <h3 style={{ margin: "0 0 15px 0", color: "#0c5460" }}>💡 Recommendations</h3>
                <ul style={{ margin: 0, paddingLeft: "20px" }}>
                  {result.recommendations.map((rec, index) => (
                    <li key={index} style={{ marginBottom: "5px" }}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
} 