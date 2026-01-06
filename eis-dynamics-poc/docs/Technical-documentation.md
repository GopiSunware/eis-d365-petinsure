Azure Services Comparison

  PetInsure360 (Deployed ✅)

  | Azure Service           | Purpose                                                            | Status      |
  |-------------------------|--------------------------------------------------------------------|-------------|
  | Azure Data Lake Gen2    | Medallion architecture storage (raw/bronze/silver/gold containers) | ✅ Deployed |
  | Azure Databricks        | ETL pipeline (Bronze → Silver → Gold transformations)              | ✅ Deployed |
  | Azure Synapse Analytics | Serverless SQL for BI queries over Delta Lake                      | ✅ Deployed |
  | Azure Data Factory      | Orchestration (optional, can use Databricks workflows)             | ✅ Deployed |
  | Azure Key Vault         | Secrets management (storage keys)                                  | ✅ Deployed |
  | Azure App Service       | Backend API hosting                                                | ✅ Deployed |
  | Azure Static Web Apps   | Frontend hosting (Customer Portal + BI Dashboard)                  | ✅ Deployed |

  Data Volume: 5,000 customers, 6,500 pets, 6,000 policies, 15,000 claims

  ---
  EIS-Dynamics POC (Not Deployed ❌)

  | Azure Service          | Purpose                                                     | Status                       |
  |------------------------|-------------------------------------------------------------|------------------------------|
  | Azure OpenAI           | GPT-4o for AI extraction, fraud detection, LangGraph agents | ❌ Planned (Terraform ready) |
  | Azure Cosmos DB        | Sync state, policies, claims, customers                     | ❌ Planned (Terraform ready) |
  | Azure Service Bus      | Event messaging (policy-sync, claim-events topics/queues)   | ❌ Planned (Terraform ready) |
  | Azure Blob Storage     | Document storage (policy-docs, claim-docs)                  | ❌ Planned (Terraform ready) |
  | Azure Key Vault        | Secrets management                                          | ❌ Planned (Terraform ready) |
  | Dataverse/Dynamics 365 | CRM integration (eis_policy, eis_claim, eis_pet entities)   | ❌ Planned (config ready)    |

  Currently Running: Local only with OpenAI/Anthropic API keys

  ---
  Side-by-Side for Data Architects

  ┌─────────────────────────────────────────────────────────────────────────────────────┐
  │                        DEMO ARCHITECTURE COMPARISON                                  │
  ├─────────────────────────────────────────────────────────────────────────────────────┤
  │                                                                                      │
  │  PETINSURE360 (Rule-Based)              EIS-DYNAMICS POC (AI-Powered)               │
  │  ─────────────────────────              ─────────────────────────────               │
  │                                                                                      │
  │  ┌─────────────────────┐                ┌─────────────────────┐                     │
  │  │ Customer Portal     │                │ Agent Portal        │                     │
  │  │ (React + Vite)      │                │ (Next.js 14)        │                     │
  │  │ :3001               │                │ :3000               │                     │
  │  └─────────┬───────────┘                └─────────┬───────────┘                     │
  │            │                                      │                                  │
  │            ▼                                      ▼                                  │
  │  ┌─────────────────────┐                ┌─────────────────────┐                     │
  │  │ FastAPI Backend     │                │ Unified Claims API  │                     │
  │  │ :8000 (Azure)       │                │ :8000 (Local)       │                     │
  │  │ • Rule Engine       │                │ • 60 endpoints      │                     │
  │  │ • Threshold Checks  │                │ • 44 LLM Tools      │                     │
  │  └─────────┬───────────┘                └─────────┬───────────┘                     │
  │            │                                      │                                  │
  │            ▼                                      ▼                                  │
  │  ┌─────────────────────┐                ┌─────────────────────┐                     │
  │  │ ADLS Gen2           │                │ LangGraph Pipeline  │                     │
  │  │ (Medallion Lake)    │                │ :8006               │                     │
  │  │ ┌─────┬─────┬─────┐ │                │ Router→Bronze→      │                     │
  │  │ │Bronze│Silver│Gold│ │                │ Silver→Gold         │                     │
  │  │ └─────┴─────┴─────┘ │                └─────────┬───────────┘                     │
  │  └─────────┬───────────┘                          │                                  │
  │            │                                      ▼                                  │
  │            ▼                                ┌─────────────────────┐                  │
  │  ┌─────────────────────┐                    │ Azure OpenAI        │                  │
  │  │ Azure Databricks    │                    │ (GPT-4o)            │                  │
  │  │ (ETL Notebooks)     │                    │ • Fraud Detection   │                  │
  │  └─────────┬───────────┘                    │ • Data Validation   │                  │
  │            │                                └─────────────────────┘                  │
  │            ▼                                                                         │
  │  ┌─────────────────────┐                    PLANNED:                                 │
  │  │ Azure Synapse       │                    ┌─────────────────────┐                  │
  │  │ (Serverless SQL)    │                    │ Cosmos DB           │                  │
  │  │ • Power BI Views    │                    │ Service Bus         │                  │
  │  │ • Ad-hoc Queries    │                    │ Dataverse/D365      │                  │
  │  └─────────────────────┘                    └─────────────────────┘                  │
  │                                                                                      │
  └─────────────────────────────────────────────────────────────────────────────────────┘

  ---
  For Data Architect Demo - Key Talking Points

  | Topic           | PetInsure360                              | EIS-Dynamics POC                                |
  |-----------------|-------------------------------------------|-------------------------------------------------|
  | Data Storage    | ADLS Gen2 + Delta Lake                    | Cosmos DB + Blob Storage                        |
  | ETL Pattern     | Databricks medallion (Bronze→Silver→Gold) | LangGraph AI agents (Router→Bronze→Silver→Gold) |
  | Query Engine    | Synapse Serverless SQL                    | FastAPI + LLM Tools                             |
  | Real-time       | WebSocket for dashboard updates           | WebSocket for pipeline visualization            |
  | Processing      | Deterministic rules (<1ms)                | AI reasoning (30-60s)                           |
  | Fraud Detection | Threshold-based (misses fraud)            | Contextual AI (catches fraud)                   |
  | Integration     | Direct ADLS writes                        | Service Bus + Dataverse sync                    |

  Key Demo Message: Same 28 scenarios, same data - but AI catches fraud that rules miss.

   Diagrams That Resonate with Data Architects

  What Data Architects Care About:

  | Priority | Concern               | Diagram Type That Helps                                   |
  |----------|-----------------------|-----------------------------------------------------------|
  | 1        | Data Flow & Lineage   | End-to-end data flow showing source → transform → consume |
  | 2        | Storage Architecture  | Medallion layers with schema evolution                    |
  | 3        | Integration Patterns  | Event-driven vs batch, sync patterns                      |
  | 4        | Scalability           | Serverless vs provisioned, auto-scale points              |
  | 5        | Security & Governance | Data boundaries, encryption, access control               |

  Diagrams I Included:

  1. End-to-End Data Flow - Shows full journey from React → API → Storage → Processing → BI
  2. Medallion Architecture Detail - Bronze/Silver/Gold with transformation rules
  3. AI Agent Pipeline (LangGraph) - Router → Bronze → Silver → Gold agents with tools
  4. Rule-Based vs AI Comparison - Side-by-side same claim, different outcomes

  Additional Diagrams Worth Adding:

  SUGGESTED: Data Governance & Security Boundary Diagram
  ─────────────────────────────────────────────────────

  ┌─────────────────────────────────────────────────────────────────┐
  │                    AZURE VIRTUAL NETWORK                         │
  │  ┌───────────────────────────────────────────────────────────┐  │
  │  │  Private Subnet                                            │  │
  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │  │
  │  │  │Cosmos DB│ │ Synapse │ │ Storage │ │ OpenAI  │          │  │
  │  │  │(Private │ │(Private │ │(Private │ │(Private │          │  │
  │  │  │Endpoint)│ │Endpoint)│ │Endpoint)│ │Endpoint)│          │  │
  │  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │  │
  │  └───────────────────────────────────────────────────────────┘  │
  │                              │                                   │
  │                              ▼                                   │
  │  ┌───────────────────────────────────────────────────────────┐  │
  │  │  App Subnet                                                │  │
  │  │  ┌─────────────────┐  ┌─────────────────┐                 │  │
  │  │  │ App Service     │  │ Azure Functions │                 │  │
  │  │  │ (Managed ID)    │  │ (Managed ID)    │                 │  │
  │  │  └────────┬────────┘  └────────┬────────┘                 │  │
  │  └───────────┼────────────────────┼──────────────────────────┘  │
  │              │                    │                              │
  │              ▼                    ▼                              │
  │  ┌───────────────────────────────────────────────────────────┐  │
  │  │  KEY VAULT (Secrets)                                       │  │
  │  │  • All credentials stored centrally                        │  │
  │  │  • Access via Managed Identity                             │  │
  │  │  • Audit logging enabled                                   │  │
  │  └───────────────────────────────────────────────────────────┘  │
  └─────────────────────────────────────────────────────────────────┘

  What Would You Like Me to Add?

  1. Data Lineage Diagram - Show column-level transformations?
  2. Cost Architecture - Which services are pay-per-use vs provisioned?
  3. Disaster Recovery - Multi-region failover diagram?
  4. DevOps Pipeline - CI/CD for data pipelines?

  