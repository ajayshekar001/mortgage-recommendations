# Knowledge Graph Based Loan Validator and Querying System - Architecture

## System Overview
This system combines FastAPI, Neo4j knowledge graph, and OpenAI LLM to provide intelligent loan application validation and sophisticated knowledge querying capabilities.

## Architecture Diagram

```mermaid
graph TB
    %% External Clients
    subgraph "External Clients"
        WEB[Web Application]
        API_CLIENT[API Client]
        MOBILE[Mobile App]
    end

    %% API Gateway Layer
    subgraph "API Gateway & Load Balancer"
        LB[Load Balancer]
        API_GATEWAY[API Gateway]
    end

    %% FastAPI Application Layer
    subgraph "FastAPI Application Layer"
        FASTAPI[FastAPI Application]
        
        subgraph "API Endpoints"
            VALIDATE[/validate-application]
            QUERY[/query-knowledge-graph]
            COMPARE[/compare-query-approaches]
            PROCESS[/process-documents]
            STATS[/knowledge-graph-stats]
            HEALTH[/health]
        end
        
        subgraph "Middleware"
            CORS[CORS Middleware]
            LOGGING[Request Logging]
            AUTH[Authentication]
        end
    end

    %% Core Services Layer
    subgraph "Core Services Layer"
        subgraph "Loan Processing Services"
            PDF_PROC[PDF Processor]
            LOAN_CONV[Loan Converter]
            LOAN_VAL[Loan Validator]
        end
        
        subgraph "Knowledge Graph Services"
            NEO4J_SERVICE[Neo4j Knowledge Graph Service]
            SEMANTIC_SEARCH[Semantic Search]
            MULTI_HOP[Multi-Hop Search]
            CONTEXT_SEARCH[Context Search]
            RELATIONSHIP_ANALYSIS[Relationship Analysis]
            AI_RECOMMENDATIONS[AI Recommendations]
        end
        
        subgraph "LLM Integration"
            OPENAI_CLIENT[OpenAI Client]
            CHAIN_OF_THOUGHT[Chain of Thought Reasoning]
            RESPONSE_GENERATION[Response Generation]
            EVALUATION_ENGINE[Evaluation Engine]
        end
    end

    %% Data Layer
    subgraph "Data Layer"
        subgraph "Neo4j Knowledge Graph"
            NEO4J[(Neo4j Database)]
            GUIDELINES[(Guidelines)]
            RELATIONSHIPS[(Relationships)]
            EMBEDDINGS[(Embeddings)]
        end
        
        subgraph "File Storage"
            UPLOADS[Upload Directory]
            TEMP_FILES[Temp Files]
        end
        
        subgraph "Configuration"
            ENV_VARS[Environment Variables]
            CONFIG[Configuration Files]
        end
    end

    %% External Services
    subgraph "External Services"
        OPENAI_API[OpenAI API]
        EMBEDDING_API[Embedding API]
    end

    %% Connections
    WEB --> LB
    API_CLIENT --> LB
    MOBILE --> LB
    
    LB --> API_GATEWAY
    API_GATEWAY --> FASTAPI
    
    FASTAPI --> CORS
    FASTAPI --> LOGGING
    FASTAPI --> AUTH
    
    VALIDATE --> LOAN_VAL
    QUERY --> NEO4J_SERVICE
    COMPARE --> NEO4J_SERVICE
    COMPARE --> OPENAI_CLIENT
    PROCESS --> PDF_PROC
    STATS --> NEO4J_SERVICE
    
    LOAN_VAL --> LOAN_CONV
    LOAN_VAL --> NEO4J_SERVICE
    LOAN_VAL --> OPENAI_CLIENT
    
    PDF_PROC --> UPLOADS
    PDF_PROC --> TEMP_FILES
    
    NEO4J_SERVICE --> NEO4J
    SEMANTIC_SEARCH --> NEO4J
    MULTI_HOP --> NEO4J
    CONTEXT_SEARCH --> NEO4J
    RELATIONSHIP_ANALYSIS --> NEO4J
    AI_RECOMMENDATIONS --> NEO4J
    
    NEO4J_SERVICE --> EMBEDDINGS
    SEMANTIC_SEARCH --> EMBEDDINGS
    
    OPENAI_CLIENT --> OPENAI_API
    EMBEDDING_API --> OPENAI_API
    
    CHAIN_OF_THOUGHT --> OPENAI_CLIENT
    RESPONSE_GENERATION --> OPENAI_CLIENT
    EVALUATION_ENGINE --> OPENAI_CLIENT
    
    ENV_VARS --> FASTAPI
    CONFIG --> FASTAPI

    %% Styling
    classDef client fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef api fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef service fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef data fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef external fill:#ffebee,stroke:#c62828,stroke-width:2px

    class WEB,API_CLIENT,MOBILE client
    class FASTAPI,VALIDATE,QUERY,COMPARE,PROCESS,STATS,HEALTH,CORS,LOGGING,AUTH api
    class PDF_PROC,LOAN_CONV,LOAN_VAL,NEO4J_SERVICE,SEMANTIC_SEARCH,MULTI_HOP,CONTEXT_SEARCH,RELATIONSHIP_ANALYSIS,AI_RECOMMENDATIONS,OPENAI_CLIENT,CHAIN_OF_THOUGHT,RESPONSE_GENERATION,EVALUATION_ENGINE service
    class NEO4J,GUIDELINES,RELATIONSHIPS,EMBEDDINGS,UPLOADS,TEMP_FILES,ENV_VARS,CONFIG data
    class OPENAI_API,EMBEDDING_API external
```

## Detailed Component Architecture

```mermaid
graph LR
    %% Knowledge Graph Core
    subgraph "Knowledge Graph Core"
        NEO4J[(Neo4j Database)]
        
        subgraph "Data Models"
            GUIDELINE[Guideline Node]
            RELATIONSHIP[Relationship Edge]
            EMBEDDING[Embedding Vector]
        end
        
        subgraph "Graph Operations"
            CREATE[Create Guidelines]
            SEARCH[Search Operations]
            TRAVERSE[Path Traversal]
            ANALYZE[Graph Analysis]
        end
    end

    %% Search Engine Layer
    subgraph "Search Engine Layer"
        subgraph "Search Types"
            SEMANTIC[Semantic Search]
            MULTI_HOP[Multi-Hop Search]
            CONTEXT[Context Search]
            RELATIONSHIPS[Relationship Analysis]
            RECOMMENDATIONS[AI Recommendations]
            GRAPH_STRUCTURE[Graph Structure]
        end
        
        subgraph "Search Features"
            EMBEDDING_SIM[Embedding Similarity]
            PATH_ANALYSIS[Path Analysis]
            QUALITY_SCORING[Quality Scoring]
            INTENT_RECOGNITION[Intent Recognition]
            DYNAMIC_HOPS[Dynamic Hop Limits]
        end
    end

    %% LLM Integration Layer
    subgraph "LLM Integration Layer"
        subgraph "LLM Services"
            DIRECT_LLM[Direct LLM]
            SEMANTIC_LLM[Semantic + LLM]
            CHAIN_OF_THOUGHT[Chain of Thought + LLM]
        end
        
        subgraph "Evaluation Engine"
            ACCURACY_EVAL[Accuracy Evaluation]
            COMPLETENESS_EVAL[Completeness Evaluation]
            RELEVANCE_EVAL[Relevance Evaluation]
            SPECIFICITY_EVAL[Specificity Evaluation]
            PRACTICAL_EVAL[Practical Value Evaluation]
        end
    end

    %% Loan Validation Layer
    subgraph "Loan Validation Layer"
        subgraph "Validation Components"
            HARD_RULES[Hard Rule Validation]
            LLM_ANALYSIS[LLM Analysis]
            KG_CONTEXT[Knowledge Graph Context]
            RISK_SCORING[Risk Scoring]
        end
        
        subgraph "Validation Features"
            DTI_CALC[DTI Calculation]
            LTV_CALC[LTV Calculation]
            CREDIT_ANALYSIS[Credit Analysis]
            INCOME_VERIFICATION[Income Verification]
            PROPERTY_ANALYSIS[Property Analysis]
        end
    end

    %% Connections
    NEO4J --> GUIDELINE
    NEO4J --> RELATIONSHIP
    NEO4J --> EMBEDDING
    
    GUIDELINE --> CREATE
    RELATIONSHIP --> TRAVERSE
    EMBEDDING --> SEARCH
    
    CREATE --> SEMANTIC
    SEARCH --> MULTI_HOP
    TRAVERSE --> CONTEXT
    ANALYZE --> RELATIONSHIPS
    
    SEMANTIC --> EMBEDDING_SIM
    MULTI_HOP --> PATH_ANALYSIS
    MULTI_HOP --> QUALITY_SCORING
    MULTI_HOP --> INTENT_RECOGNITION
    MULTI_HOP --> DYNAMIC_HOPS
    
    SEMANTIC --> SEMANTIC_LLM
    MULTI_HOP --> CHAIN_OF_THOUGHT
    RECOMMENDATIONS --> DIRECT_LLM
    
    DIRECT_LLM --> ACCURACY_EVAL
    SEMANTIC_LLM --> COMPLETENESS_EVAL
    CHAIN_OF_THOUGHT --> RELEVANCE_EVAL
    
    ACCURACY_EVAL --> HARD_RULES
    COMPLETENESS_EVAL --> LLM_ANALYSIS
    RELEVANCE_EVAL --> KG_CONTEXT
    
    HARD_RULES --> DTI_CALC
    HARD_RULES --> LTV_CALC
    LLM_ANALYSIS --> CREDIT_ANALYSIS
    KG_CONTEXT --> INCOME_VERIFICATION
    RISK_SCORING --> PROPERTY_ANALYSIS

    %% Styling
    classDef core fill:#e3f2fd,stroke:#1565c0,stroke-width:3px
    classDef search fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    classDef llm fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef validation fill:#fce4ec,stroke:#ad1457,stroke-width:2px

    class NEO4J,GUIDELINE,RELATIONSHIP,EMBEDDING,CREATE,SEARCH,TRAVERSE,ANALYZE core
    class SEMANTIC,MULTI_HOP,CONTEXT,RELATIONSHIPS,RECOMMENDATIONS,GRAPH_STRUCTURE,EMBEDDING_SIM,PATH_ANALYSIS,QUALITY_SCORING,INTENT_RECOGNITION,DYNAMIC_HOPS search
    class DIRECT_LLM,SEMANTIC_LLM,CHAIN_OF_THOUGHT,ACCURACY_EVAL,COMPLETENESS_EVAL,RELEVANCE_EVAL,SPECIFICITY_EVAL,PRACTICAL_EVAL llm
    class HARD_RULES,LLM_ANALYSIS,KG_CONTEXT,RISK_SCORING,DTI_CALC,LTV_CALC,CREDIT_ANALYSIS,INCOME_VERIFICATION,PROPERTY_ANALYSIS validation
```

## Data Flow Architecture

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant Validator as Loan Validator
    participant KG as Knowledge Graph
    participant LLM as OpenAI LLM
    participant Neo4j as Neo4j Database

    %% Loan Validation Flow
    Client->>API: POST /validate-application
    API->>Validator: Validate Application
    Validator->>Validator: Calculate DTI/LTV
    Validator->>Validator: Apply Hard Rules
    Validator->>KG: Get Relevant Guidelines
    KG->>Neo4j: Query Guidelines
    Neo4j-->>KG: Return Guidelines
    KG-->>Validator: Return Context
    Validator->>LLM: Analyze with Context
    LLM-->>Validator: Return Analysis
    Validator->>Validator: Generate Risk Score
    Validator-->>API: Return Validation Result
    API-->>Client: Return Response

    %% Knowledge Query Flow
    Client->>API: POST /query-knowledge-graph
    API->>KG: Execute Search
    KG->>Neo4j: Perform Search Operation
    Neo4j-->>KG: Return Results
    KG->>KG: Process Results
    KG-->>API: Return Search Results
    API-->>Client: Return Response

    %% Comparison Flow
    Client->>API: POST /compare-query-approaches
    API->>LLM: Direct LLM Response
    LLM-->>API: Return Response
    API->>KG: Semantic Search
    KG->>Neo4j: Query Guidelines
    Neo4j-->>KG: Return Guidelines
    KG-->>API: Return Search Results
    API->>LLM: Generate Semantic Response
    LLM-->>API: Return Response
    API->>KG: Multi-Hop Search
    KG->>Neo4j: Complex Query
    Neo4j-->>KG: Return Paths
    KG-->>API: Return Path Analysis
    API->>LLM: Chain of Thought Response
    LLM-->>API: Return Response
    API->>LLM: Evaluate All Approaches
    LLM-->>API: Return Evaluation
    API-->>Client: Return Comparison
```

## Technology Stack

```mermaid
graph TB
    subgraph "Frontend Layer"
        WEB[Web Application]
        API_CLIENT[API Client]
    end

    subgraph "Backend Framework"
        FASTAPI[FastAPI]
        UVICORN[Uvicorn ASGI Server]
    end

    subgraph "Database Layer"
        NEO4J[Neo4j Graph Database]
        CYPHER[Cypher Query Language]
    end

    subgraph "AI/ML Layer"
        OPENAI[OpenAI GPT-4]
        EMBEDDINGS[Text Embeddings]
        VECTOR_SIM[Vector Similarity]
    end

    subgraph "Processing Layer"
        PDF_PROC[PDF Processing]
        DOC_CONV[Document Conversion]
        DATA_EXTR[Data Extraction]
    end

    subgraph "Infrastructure"
        DOCKER[Docker Containerization]
        ENV[Environment Management]
        LOGGING[Structured Logging]
    end

    WEB --> FASTAPI
    API_CLIENT --> FASTAPI
    FASTAPI --> UVICORN
    FASTAPI --> NEO4J
    NEO4J --> CYPHER
    FASTAPI --> OPENAI
    FASTAPI --> EMBEDDINGS
    EMBEDDINGS --> VECTOR_SIM
    FASTAPI --> PDF_PROC
    PDF_PROC --> DOC_CONV
    DOC_CONV --> DATA_EXTR
    FASTAPI --> DOCKER
    DOCKER --> ENV
    FASTAPI --> LOGGING

    classDef frontend fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef backend fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef database fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef ai fill:#fce4ec,stroke:#ad1457,stroke-width:2px
    classDef processing fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef infra fill:#ffebee,stroke:#c62828,stroke-width:2px

    class WEB,API_CLIENT frontend
    class FASTAPI,UVICORN backend
    class NEO4J,CYPHER database
    class OPENAI,EMBEDDINGS,VECTOR_SIM ai
    class PDF_PROC,DOC_CONV,DATA_EXTR processing
    class DOCKER,ENV,LOGGING infra
```

## Key Features and Capabilities

### 1. **Knowledge Graph Core**
- **Neo4j Database**: Stores mortgage guidelines as nodes with relationships
- **Embedding Vectors**: Semantic representations for similarity search
- **Graph Traversal**: Multi-hop path discovery and analysis

### 2. **Advanced Search Capabilities**
- **Semantic Search**: Find relevant guidelines using embedding similarity
- **Multi-Hop Search**: Discover connections through multiple guideline relationships
- **Context Search**: Gather comprehensive context around topics
- **Relationship Analysis**: Analyze connections between guidelines
- **AI Recommendations**: Generate actionable recommendations

### 3. **LLM Integration**
- **Direct LLM**: Pure AI responses without knowledge base
- **Semantic + LLM**: Knowledge-enhanced responses
- **Chain of Thought**: Sophisticated reasoning with knowledge graph paths
- **Evaluation Engine**: Comprehensive assessment of response quality

### 4. **Loan Validation System**
- **Hard Rule Validation**: Traditional underwriting rules
- **LLM Analysis**: AI-powered risk assessment
- **Knowledge Graph Context**: Guideline-based validation
- **Risk Scoring**: Comprehensive risk evaluation

### 5. **System Features**
- **RESTful API**: FastAPI-based endpoints
- **Real-time Processing**: Immediate validation and querying
- **Scalable Architecture**: Containerized deployment
- **Comprehensive Logging**: Detailed operation tracking
- **Error Handling**: Robust error management

## Benefits

1. **Intelligent Validation**: Combines traditional rules with AI reasoning
2. **Knowledge Discovery**: Uncovers hidden connections between guidelines
3. **Comprehensive Analysis**: Multi-faceted approach to loan assessment
4. **Scalable Architecture**: Handles high-volume processing
5. **Real-time Insights**: Immediate access to knowledge and validation
6. **Continuous Learning**: System improves with more data and usage 