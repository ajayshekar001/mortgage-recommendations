# Loan Application Processing and Validation System

A comprehensive system for processing loan applications and validating them against standard mortgage underwriting guidelines.

## System Overview

The system consists of two main modules:
1. PDF Processing Module: Converts loan documents into URLA (Uniform Residential Loan Application) format
2. Loan Validation Module: Validates loan applications against underwriting rules

## Underwriting Guidelines

The system implements standard mortgage underwriting guidelines based on Fannie Mae and Freddie Mac (GSE) requirements.

### 1. Debt-to-Income (DTI) Ratios
- Maximum DTI Ratio: 43%
- Risk Thresholds:
  - Low Risk: Below 36%
  - Medium Risk: 36-43%
  - High Risk: Above 43%
- Front-end ratio (housing expenses): Maximum 28%
- Back-end ratio (total debt): Maximum 36%
- Up to 43% allowed with compensating factors
- Above 43% requires strong compensating factors

### 2. Loan-to-Value (LTV) Ratios
- Maximum LTV Ratio: 97%
- Risk Thresholds:
  - Low Risk: Below 80% (No PMI required)
  - Medium Risk: 80-90% (PMI required)
  - High Risk: 90-97% (Higher PMI and stricter requirements)
- Above 97% not typically allowed for conventional loans

### 3. Credit Score Requirements
- Minimum Credit Score: 620
- Risk Thresholds:
  - Excellent: 760+
  - Good: 700-759
  - Fair: 660-699
  - Poor: 620-659
- Below 620 not eligible for conventional loans

### 4. Down Payment Requirements
- Minimum Down Payment: 3%
- First-time homebuyers: 3% minimum
- Non-first-time homebuyers: 5% minimum
- 20% required to avoid PMI

### 5. Required Documentation
- Income Verification:
  - W-2 forms for the last 2 years
  - Most recent pay stubs covering 30 days
  - Tax returns for the last 2 years
- Asset Verification:
  - Bank statements for the last 2 months
  - Statements for all assets (checking, savings, investments)
- Identity Verification:
  - Government-issued photo ID
- Property Documentation:
  - Signed purchase agreement
  - Homeowners insurance quote
- Additional Requirements:
  - Credit report authorization
  - Employment verification letter

### 6. Risk Scoring System
Risk weights for different factors:
- High DTI: 25%
- High LTV: 25%
- Low Credit Score: 20%
- Missing Documentation: 15%
- Low Down Payment: 15%

Risk reduction factors:
- Strong Income: 10% reduction
- Low LTV: 15% reduction
- High Reserves: 10% reduction

### 7. Reserves Requirements
- Standard requirement: 2-6 months of reserves
- Calculated as: Total liquid assets / Monthly mortgage payment
- More reserves required for higher risk loans
- Can be used as a compensating factor

## API Endpoints

### 1. Process Documents
```http
POST /process-documents
```
Process uploaded loan documents and convert them to URLA format.

### 2. Validate Application
```http
POST /validate-application
```
Validate loan application data against underwriting rules.

### 3. Health Check
```http
GET /health
```
Check the health status of the API.

## Getting Started

This guide will walk you through setting up the complete AI-powered loan processing system, including:
- Processing the Fannie Mae Selling Guide PDF into a knowledge graph
- Setting up vector embeddings for semantic search
- Creating intelligent relationships between guidelines
- Running both the Python backend and React frontend servers
- Testing the advanced KG+LLM reasoning capabilities

### Prerequisites

- Python 3.9+
- Node.js 18+
- Neo4j Database (running on bolt://localhost:7687)
- OpenAI API Key
- Google Generative AI API Key

### Environment Setup

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Install React dependencies:**
```bash
cd compare-query-ui
npm install
cd ..
```

3. **Setup environment variables:**
Create a `.env` file in the root directory:
```bash
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4jAjay
```

### Quick Setup (All Steps)

For experienced users, run the complete pipeline in sequence:
```bash
# Setup environment
pip install -r requirements.txt
cd compare-query-ui && npm install && cd ..

# Process data pipeline
python app/scripts/init_db.py
python app/scripts/parse_and_chunk_pdf.py
python app/scripts/generate_embeddings_openai.py
python app/scripts/sync_guidelines_to_neo4j.py

# Add relationships
python app/scripts/add_sequential_relationships.py
python app/scripts/add_section_relationships.py
python app/scripts/add_content_similarity_relationships.py

# Start servers (in separate terminals)
python run_server.py &
cd compare-query-ui && npm start
```

### Complete Setup Process (Detailed)

#### Step 1: Initialize Database
```bash
python app/scripts/init_db.py
```

#### Step 2: Process Fannie Mae Guidelines (Complete Pipeline)

**2a. Parse PDF and Create Chunks:**
```bash
python app/scripts/parse_and_chunk_pdf.py
```
*This processes the Fannie Mae Selling Guide PDF and creates structured chunks*

**2b. Generate Vector Embeddings:**
```bash
python app/scripts/generate_embeddings_openai.py
```
*This creates OpenAI embeddings for semantic search capabilities*

**2c. Load Guidelines to Neo4j Database:**
```bash
python app/scripts/sync_guidelines_to_neo4j.py
```
*This loads all guidelines as nodes in the Neo4j knowledge graph*

#### Step 3: Create Knowledge Graph Relationships

**3a. Add Sequential Relationships:**
```bash
python app/scripts/add_sequential_relationships.py
```
*Creates NEXT relationships between consecutive guidelines*

**3b. Add Section-based Relationships:**
```bash
python app/scripts/add_section_relationships.py
```
*Creates SAME_SECTION relationships for guidelines in the same section*

**3c. Add Content Similarity Relationships:**
```bash
python app/scripts/add_content_similarity_relationships.py
```
*Creates RELATED relationships based on content similarity*

#### Step 4: Start the Servers

**4a. Start the Python Backend Server:**
```bash
python run_server.py
```
*Or alternatively:*
```bash
uvicorn app.api.main:app --reload --host localhost --port 8000
```
*Backend will be available at: http://localhost:8000*

**4b. Start the React Frontend Server:**
```bash
cd compare-query-ui
npm start
```
*Frontend will be available at: http://localhost:3000*

### Verification Commands

**Test Neo4j Connection:**
```bash
python app/scripts/test_neo4j_connection.py
```

**Test Knowledge Graph API:**
```bash
python app/scripts/test_knowledge_graph_api.py
```

**Run System Tests:**
```bash
python app/scripts/run_tests.py
```

### Quick Test Commands

**Test Loan Validation API:**
```bash
curl -X POST http://localhost:8000/validate-application \
  -H "Content-Type: application/json" \
  -d '{
    "loanApplication": {
      "borrower": {
        "firstName": "John",
        "lastName": "Smith",
        "ssn": "123-45-6789",
        "dateOfBirth": "1985-06-15",
        "maritalStatus": "Married",
        "contact": {
          "email": "john.smith@email.com",
          "phone": "555-0123"
        },
        "residences": [
          {
            "address": {
              "street": "123 Main St",
              "city": "San Francisco",
              "state": "CA",
              "zipCode": "94105"
            },
            "type": "Rent",
            "duration": 24
          }
        ],
        "employment": [
          {
            "employer": "Tech Corp",
            "position": "Software Engineer",
            "startDate": "2020-01-01",
            "income": {
              "baseSalary": 150000,
              "bonus": 25000,
              "overtime": 0,
              "commission": 0
            }
          }
        ],
        "assets": [
          {
            "type": "Checking",
            "institution": "Bank of America",
            "accountNumber": "****1234",
            "balance": 50000
          },
          {
            "type": "Savings",
            "institution": "Bank of America",
            "accountNumber": "****5678",
            "balance": 100000
          }
        ],
        "liabilities": [
          {
            "type": "Car Loan",
            "creditor": "Auto Finance Co",
            "accountNumber": "****9012",
            "monthlyPayment": 500,
            "unpaidBalance": 15000
          }
        ]
      },
      "loan": {
        "amount": 800000,
        "purpose": "Purchase",
        "property": {
          "address": {
            "street": "456 Market St",
            "city": "San Francisco",
            "state": "CA",
            "zipCode": "94105"
          },
          "value": 1000000,
          "occupancy": "Primary",
          "type": "Single Family"
        },
        "interestRate": 6.5,
        "term": 360
      },
      "declarations": {
        "bankruptcy": false,
        "foreclosure": false,
        "lawsuit": false,
        "delinquentDebt": false
      },
      "submissionMetadata": {
        "submissionTime": "2024-03-20T10:00:00Z",
        "submitterEmail": "loan.officer@bank.com",
        "applicationId": "APP-2024-001"
      }
    }
  }'
```

Expected Response:
```json
{
  "application_id": "APP-2024-001",
  "is_approved": false,
  "risk_score": 0.0,
  "risk_flags": ["missing_docs"],
  "recommendations": [
    "Please provide W-2 forms for the last 2 years",
    "Please provide most recent pay stubs covering 30 days",
    "Please provide tax returns for the last 2 years",
    "Please provide bank statements for the last 2 months",
    "Please provide government-issued photo ID",
    "Please provide signed purchase agreement",
    "Please provide homeowners insurance quote",
    "Please provide credit report authorization",
    "Please provide employment verification letter"
  ],
  "dti_ratio": 0.0178,
  "ltv_ratio": 0.8,
  "explanation": "Application not approved due to missing required documentation. The application shows a DTI ratio of 1.78% and an LTV ratio of 80%. The down payment of 20% meets the minimum requirement. Missing required documentation."
}
```

**Test Knowledge Graph Query API:**
```bash
curl -X POST http://localhost:8000/query-knowledge-graph \
  -H "Content-Type: application/json" \
  -d '{
    "query": "DTI ratio requirements",
    "search_type": "semantic",
    "max_results": 5
  }'
```

**Test Compare Query Approaches (Advanced Reasoning):**
```bash
curl -X POST http://localhost:8000/compare-query-approaches \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the DTI requirements for borrowers with compensating factors?",
    "max_results": 8,
    "max_hops": 4,
    "include_chain_of_thought": true
  }'
```

**Health Check:**
```bash
curl http://localhost:8000/health
```

### Frontend Application Usage

1. **Access the application**: Open http://localhost:3000 in your browser

2. **Loan Validation Page**: 
   - Click "Load Sample Data" to auto-fill a loan application
   - Click "Validate Loan Application" to see AI-powered approval decisions
   - View detailed explanations, risk scores, and recommendations

3. **Compare Query Page**:
   - Enter complex mortgage underwriting questions
   - See side-by-side comparison of different AI approaches
   - Observe the superior accuracy of Knowledge Graph + LLM reasoning

### Data Processing Pipeline Summary

The complete pipeline processes the Fannie Mae Selling Guide through these stages:

1. **PDF → Chunks**: Extracts and structures content from the 1000+ page PDF
2. **Chunks → Embeddings**: Creates semantic vector representations for each chunk
3. **Embeddings → Neo4j**: Loads structured data into the knowledge graph
4. **Relationships**: Creates three types of intelligent connections:
   - **Sequential** (NEXT): Document flow relationships
   - **Sectional** (SAME_SECTION): Content grouping relationships  
   - **Semantic** (RELATED): Content similarity relationships

### Troubleshooting

**Common Issues:**

1. **Neo4j Connection Failed**: 
   - Ensure Neo4j is running on bolt://localhost:7687
   - Check username/password in .env file

2. **OpenAI API Errors**:
   - Verify OPENAI_API_KEY in .env file
   - Check API key has sufficient credits

3. **Missing Embeddings**:
   - Run the embedding generation script: `python app/scripts/generate_embeddings_openai.py`
   - Ensure chunks file exists: `uploads/selling_guide_chunks.json`

4. **React Server Issues**:
   - Clear node_modules: `rm -rf compare-query-ui/node_modules && cd compare-query-ui && npm install`
   - Check Node.js version: Should be 18+

### Advanced Features

**Knowledge Graph Visualization:**
```bash
python app/scripts/visualize_knowledge_graph.py
```

**Advanced Graph Queries:**
```bash
python app/scripts/advanced_graph_queries.py
```

**Enhance Semantic Search:**
```bash
python app/scripts/enhance_semantic_search.py
```

## Project Structure
```
app/
├── api/
│   └── main.py
├── models/
│   ├── loan_application.py
│   └── external_loan_application.py
├── services/
│   ├── loan_validator.py
│   ├── loan_converter.py
│   └── pdf_processor.py
└── utils/
    └── helpers.py
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Available Gemini Models

The following Gemini models are available for use with the Google Generative AI API:

- **models/embedding-gecko-001** (supported methods: ['embedText', 'countTextTokens'])
- **models/gemini-1.0-pro-vision-latest** (supported methods: ['generateContent', 'countTokens'])
- **models/gemini-pro-vision** (supported methods: ['generateContent', 'countTokens'])
- **models/gemini-1.5-pro-latest** (supported methods: ['generateContent', 'countTokens'])
- **models/gemini-1.5-pro-002** (supported methods: ['generateContent', 'countTokens', 'createCachedContent'])
- **models/gemini-1.5-pro** (supported methods: ['generateContent', 'countTokens'])
- **models/gemini-1.5-flash-latest** (supported methods: ['generateContent', 'countTokens'])
- **models/gemini-1.5-flash** (supported methods: ['generateContent', 'countTokens'])
- **models/gemini-1.5-flash-002** (supported methods: ['generateContent', 'countTokens', 'createCachedContent'])
- **models/gemini-1.5-flash-8b** (supported methods: ['createCachedContent', 'generateContent', 'countTokens'])
- **models/gemini-1.5-flash-8b-001** (supported methods: ['createCachedContent', 'generateContent', 'countTokens'])
- **models/gemini-1.5-flash-8b-latest** (supported methods: ['createCachedContent', 'generateContent', 'countTokens'])
- **models/gemini-2.5-pro-exp-03-25** (supported methods: ['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent'])
- **models/gemini-2.5-pro-preview-03-25** (supported methods: ['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent'])
- **models/gemini-2.5-flash-preview-04-17** (supported methods: ['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent'])
- **models/gemini-2.5-flash-preview-05-20** (supported methods: ['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent'])
- **models/gemini-2.5-flash-preview-04-17-thinking** (supported methods: ['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent'])
- **models/gemini-2.5-pro-preview-05-06** (supported methods: ['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent'])
- **models/gemini-2.5-pro-preview-06-05** (supported methods: ['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent'])
- **models/gemini-2.0-flash-exp** (supported methods: ['generateContent', 'countTokens', 'bidiGenerateContent'])
- **models/gemini-2.0-flash** (supported methods: ['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent'])
- **models/gemini-2.0-flash-001** (supported methods: ['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent'])
- **models/gemini-2.0-flash-exp-image-generation** (supported methods: ['generateContent', 'countTokens', 'bidiGenerateContent'])
- **models/gemini-2.0-flash-lite-001** (supported methods: ['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent'])
- **models/gemini-2.0-flash-lite** (supported methods: ['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent'])
- **models/gemini-2.0-flash-preview-image-generation** (supported methods: ['generateContent', 'countTokens'])
- **models/gemini-2.0-flash-lite-preview-02-05** (supported methods: ['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent'])
- **models/gemini-2.0-flash-lite-preview** (supported methods: ['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent'])
- **models/gemini-2.0-pro-exp** (supported methods: ['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent'])
- **models/gemini-2.0-pro-exp-02-05** (supported methods: ['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent'])
- **models/gemini-exp-1206** (supported methods: ['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent'])
- **models/gemini-2.0-flash-thinking-exp-01-21** (supported methods: ['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent'])
- **models/gemini-2.0-flash-thinking-exp** (supported methods: ['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent'])
- **models/gemini-2.0-flash-thinking-exp-1219** (supported methods: ['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent'])
- **models/gemini-2.5-flash-preview-tts** (supported methods: ['countTokens', 'generateContent'])
- **models/gemini-2.5-pro-preview-tts** (supported methods: ['countTokens', 'generateContent'])
- **models/learnlm-2.0-flash-experimental** (supported methods: ['generateContent', 'countTokens'])
- **models/gemma-3-1b-it** (supported methods: ['generateContent', 'countTokens'])
- **models/gemma-3-4b-it** (supported methods: ['generateContent', 'countTokens'])
- **models/gemma-3-12b-it** (supported methods: ['generateContent', 'countTokens'])
- **models/gemma-3-27b-it** (supported methods: ['generateContent', 'countTokens'])
- **models/gemma-3n-e4b-it** (supported methods: ['generateContent', 'countTokens'])
- **models/embedding-001** (supported methods: ['embedContent'])
- **models/text-embedding-004** (supported methods: ['embedContent'])
- **models/gemini-embedding-exp-03-07** (supported methods: ['embedContent', 'countTextTokens', 'countTokens'])
- **models/gemini-embedding-exp** (supported methods: ['embedContent', 'countTextTokens', 'countTokens'])
- **models/aqa** (supported methods: ['generateAnswer'])
- **models/imagen-3.0-generate-002** (supported methods: ['predict'])
- **models/veo-2.0-generate-001** (supported methods: ['predictLongRunning'])
- **models/gemini-2.5-flash-preview-native-audio-dialog** (supported methods: ['countTokens', 'bidiGenerateContent'])
- **models/gemini-2.5-flash-preview-native-audio-dialog-rai-v3** (supported methods: ['countTokens', 'bidiGenerateContent'])
- **models/gemini-2.5-flash-exp-native-audio-thinking-dialog** (supported methods: ['countTokens', 'bidiGenerateContent'])
- **models/gemini-2.0-flash-live-001** (supported methods: ['bidiGenerateContent', 'countTokens'])

## Fannie Mae Selling Guide as the Foundation for Loan Approval

This system is built on the authoritative [Fannie Mae Selling Guide](https://singlefamily.fanniemae.com/media/42746/display), which is the industry standard for determining eligibility and requirements for selling loans to Fannie Mae. The guide provides comprehensive, up-to-date standards for:

- **Borrower eligibility** (credit score, income, employment, etc.)
- **Property requirements**
- **Loan-to-value (LTV) and debt-to-income (DTI) ratios**
- **Documentation standards**
- **Compensating factors and exceptions**
- **Special loan programs and products**
- **Risk assessment and mitigation**

### How the Guide is Used in This System

- **Automated Underwriting:**
  - The rules and thresholds from the Selling Guide are encoded into the knowledge graph and validation logic, ensuring every application is checked against Fannie Mae's standards.
- **Manual Review:**
  - For edge cases or exceptions, underwriters can refer directly to the guide for clarification and to justify decisions.
- **Knowledge Graph Integration:**
  - The system extracts rules, thresholds, and relationships from the Selling Guide and represents them as nodes and edges in a knowledge graph. This enables automated, explainable decision-making and easy updates when the guide changes.
- **Audit and Compliance:**
  - Using the Selling Guide as the source ensures the process is compliant with Fannie Mae's requirements, which is critical for loan salability and audit readiness.

**In summary:**
> The Fannie Mae Selling Guide is the gold standard for loan application approval processes for any lender intending to sell loans to Fannie Mae. This system's use of a knowledge graph and reasoning engine based on this guide is a best practice for modern, explainable, and compliant mortgage underwriting.

## Why Use a Knowledge Graph for Fannie Mae Guidelines?

Encoding the Fannie Mae Selling Guide as a structured knowledge graph provides significant advantages over relying solely on a large language model (LLM) for loan decision making:

### Key Advantages
- **Explicit, Auditable Rules:**
  - Every guideline, threshold, and exception is explicitly represented as a node or relationship, making decisions traceable and compliant.
- **Explainability:**
  - The system can show *why* a loan was approved or denied, referencing the exact rules and relationships from the Selling Guide.
- **Consistency:**
  - The knowledge graph enforces consistent application of rules across all applications, reducing variability and errors.
- **Updatability:**
  - When the Selling Guide changes, you can update or add nodes/edges in the graph without retraining or re-prompting an LLM.
- **Hybrid Reasoning:**
  - The knowledge graph handles all hard rules and relationships, while the LLM can be used for soft reasoning, edge cases, or generating explanations—always grounded in the graph.
- **Semantic Search & Discovery:**
  - Enables advanced queries, such as finding all guidelines related to DTI and compensating factors, or exploring dependencies between rules.
- **Chain-of-Thought and Multi-Guideline Reasoning:**
  - Supports step-by-step, multi-hop reasoning (e.g., "if DTI is high, check for compensating factors, then check reserves…").

### Why Not Just Use an LLM?
- LLMs may provide plausible-sounding but unverifiable explanations, and their responses can vary depending on prompt phrasing or context.
- LLMs alone are less auditable, harder to update, and may hallucinate or miss multi-step dependencies.

### Best Practice: Combine Both
- **Knowledge Graph:** Encodes the rules, relationships, and structure of the Selling Guide for trustworthy, explainable, and compliant decision making.
- **LLM:** Used for natural language explanations, handling ambiguous cases, or extracting new rules from unstructured text.

**In summary:**
> Building a knowledge graph from the full Fannie Mae Selling Guide is a significant advantage. It provides structure, explainability, and compliance that pure LLM-based systems cannot guarantee. This hybrid approach is the future of trustworthy, AI-powered underwriting.

## Loading the Full Fannie Mae Selling Guide PDF into the Knowledge Graph

To enable advanced, explainable, and multi-hop reasoning over the entire Fannie Mae Selling Guide, the following process is used to load the 1000+ page PDF into the knowledge graph:

### Step-by-Step Process

1. **PDF Parsing & Chunking**
   - Extract text from the PDF, breaking it into manageable, meaningful chunks (e.g., by section, guideline, or paragraph).
   - Preserve structure: Capture section headers, guideline numbers, and references.

2. **Node Creation**
   - Each chunk/section/guideline becomes a node in the knowledge graph.
   - Node schema includes:
     - `id`
     - `title` (section/guideline heading)
     - `content` (text of the chunk)
     - `category` (e.g., DTI, Credit, Property, etc.)
     - `source_reference` (page number, section number)
     - `embedding` (for semantic search)
     - `metadata` (thresholds, requirements, etc.)

3. **Relationship Extraction**
   - Detect references to other guidelines/sections (e.g., "see Section B3-5.3-01").
   - Create edges for:
     - `depends_on`
     - `supplements`
     - `contradicts`
     - `exception_to`
     - `example_of`
   - Link nodes based on these relationships for multi-hop reasoning.

4. **Semantic Embedding**
   - Generate an embedding for each node using a language model or embedding model.
   - Store the embedding in the node for fast semantic search.

5. **Chain-of-Thought/Reasoning Support**
   - The graph structure (nodes + edges) enables multi-hop queries (e.g., "If DTI is high, what compensating factors are allowed, and what documentation is required?").
   - Relationships allow traversing the graph for complex, explainable reasoning.

---

**This approach enables the system to perform advanced, explainable, and compliant loan validation by leveraging the full depth and structure of the Fannie Mae Selling Guide.**

## Neo4j Integration

You can programmatically add relationships in Neo4j based on your specific needs. Here are some possibilities:

- **Sequential Relationships:** Link each guideline to the next as "NEXT" or "SEQUENTIAL".
- **Section/Subsection Relationships:** Link all guidelines in the same section or subsection as "SAME_SECTION" or "SAME_SUBSECTION".
- **Keyword/Content Similarity:** Use embeddings or keyword overlap to link similar guidelines as "RELATED".
- **Explicit Metadata:** If your data has fields like "prerequisite_for" or "related_to", use those.

For example, you can add sequential relationships with a script like this:

```python
from app.services.neo4j_knowledge_graph import Neo4jKnowledgeGraph
import json
from pathlib import Path

def add_sequential_relationships():
    kg = Neo4jKnowledgeGraph()
    guidelines_path = Path("/Users/shekar/blend/hackathon/uploads/selling_guide_chunks_with_openai_embeddings.json")
    with open(guidelines_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    # Sort by id or any order you want
    chunks = sorted(chunks, key=lambda x: x.get('id', ''))
    for i in range(len(chunks) - 1):
        source_id = chunks[i].get('id', '')
        target_id = chunks[i+1].get('id', '')
        if source_id and target_id:
            kg.add_relationship(source_id, target_id, "NEXT")
    kg.close()

if __name__ == "__main__":
    add_sequential_relationships()
```

Or add relationships by section:

```python
from collections import defaultdict

def add_section_relationships():
    kg = Neo4jKnowledgeGraph()
    guidelines_path = Path("/Users/shekar/blend/hackathon/uploads/selling_guide_chunks_with_openai_embeddings.json")
    with open(guidelines_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    # Group by section
    section_map = defaultdict(list)
    for chunk in chunks:
        section = chunk.get('metadata', {}).get('section', '')
        if section:
            section_map[section].append(chunk.get('id', ''))

    # Add SAME_SECTION relationships
    for ids in section_map.values():
        for i in range(len(ids)):
            for j in range(i+1, len(ids)):
                kg.add_relationship(ids[i], ids[j], "SAME_SECTION")
    kg.close()

if __name__ == "__main__":
    add_section_relationships()
```

You can combine or modify these scripts to fit your business rules, such as using content similarity, explicit metadata, or even LLMs to suggest relationships. 

## System Architecture

Here's a high-level system diagram of the components and their interactions:

```
+------------------------+     +------------------------+     +------------------------+
|                        |     |                        |     |                        |
|  Fannie Mae Selling    |     |  PDF Processing &      |     |  Neo4j Knowledge      |
|  Guide PDF             |---->|  Chunking              |---->|  Graph                 |
|                        |     |                        |     |                        |
+------------------------+     +------------------------+     +------------------------+
                                                                    |
                                                                    v
+------------------------+     +------------------------+     +------------------------+
|                        |     |                        |     |                        |
|  Advanced Graph        |     |  Relationship          |     |  Guidelines as         |
|  Queries & Analytics   |<----|  Types                 |<----|  Nodes                 |
|                        |     |                        |     |                        |
+------------------------+     +------------------------+     +------------------------+
        |                              |
        |                              |
        v                              v
+------------------------+     +------------------------+
|                        |     |                        |
|  Semantic Search       |     |  Relationship          |
|  (using embeddings)    |     |  Types:                |
|                        |     |  - NEXT               |
+------------------------+     |  - SAME_SECTION       |
                               |  - RELATED            |
                               |  (content similarity) |
                               +------------------------+
```

### Key Components:

1. **Data Source**
   - Fannie Mae Selling Guide PDF
   - Contains mortgage underwriting guidelines

2. **Processing Layer**
   - PDF Processing & Chunking
   - Extracts text and metadata
   - Creates manageable chunks

3. **Neo4j Knowledge Graph**
   - Guidelines stored as nodes
   - Properties:
     - id
     - title
     - content
     - section
     - subsection
     - embedding

4. **Relationship Types**
   - NEXT (Sequential)
   - SAME_SECTION
   - RELATED (Content Similarity)

5. **Advanced Features**
   - Semantic Search using embeddings
   - Graph-based analytics
   - Relationship traversal

6. **Integration Points**
   - Neo4j Browser for visualization
   - API endpoints for application integration
   - Query capabilities for advanced analysis