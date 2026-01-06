Summary

  Both projects are pet insurance platforms but serve different purposes and have different architectures:

  | Aspect        | PetInsure360                             | EIS-Dynamics POC                               |
  |---------------|------------------------------------------|------------------------------------------------|
  | Primary Focus | Data Platform & Analytics                | Operational Claims Processing                  |
  | Target        | IPH (Independence Pet Holdings) demo     | EIS Insurance Suite → Dynamics 365 integration |
  | Architecture  | Medallion Lakehouse (Bronze/Silver/Gold) | Microservices with Event-Driven messaging      |

  ---
  Architecture Comparison

  PetInsure360:                          EIS-Dynamics POC:
  ─────────────                          ─────────────────
  React SPA                              Next.js 14 Agent Portal
      │                                      │
  FastAPI (single backend)               Azure API Management (APIM)
      │                                      │
  ADLS Gen2 (JSON files)                 ┌───┴───────────────┐
      │                                  │         │         │
  Databricks ETL                     WS2 AI    WS3 EIS    WS5 Rating
  (Bronze→Silver→Gold)               Claims    Sync       Engine
      │                                  │         │         │
  Delta Lake                         Azure Service Bus
      │                                  │
  BI Dashboard                       ┌───┴───┐
                                  Cosmos   Dataverse
                                    DB      (D365)

  ---
  Feature Comparison

  | Feature        | PetInsure360                                  | EIS-Dynamics POC                           |
  |----------------|-----------------------------------------------|--------------------------------------------|
  | Frontend       | React + Vite (Customer Portal + BI Dashboard) | Next.js 14 (Agent Portal only)             |
  | Backend        | Single FastAPI                                | 3 Microservices (8001, 8002, 8003)         |
  | Database       | Delta Lake (ADLS Gen2)                        | Cosmos DB + Dataverse                      |
  | ETL            | Databricks notebooks (Bronze→Silver→Gold)     | Real-time via Service Bus                  |
  | AI/GenAI       | Multi-agent claims processor                  | GPT-4o FNOL + Fraud Detection              |
  | OCR            | -                                             | Azure Document Intelligence (vet invoices) |
  | Infrastructure | Terraform (basic)                             | Terraform (modular - 10 modules)           |
  | Testing        | -                                             | pytest + e2e tests                         |
  | Messaging      | WebSocket (Socket.IO)                         | Azure Service Bus (queues/topics)          |
  | API Gateway    | None                                          | Azure API Management                       |

  ---
  Key Differences

  1. Data Architecture

  | PetInsure360                    | EIS-Dynamics POC                       |
  |---------------------------------|----------------------------------------|
  | Batch ETL (medallion lakehouse) | Real-time event-driven                 |
  | Analytics-focused (CDP, KPIs)   | Operations-focused (claims processing) |
  | Gold layer tables for BI        | Transactional data in Cosmos/Dataverse |

  2. AI Capabilities

  | PetInsure360                | EIS-Dynamics POC                   |
  |-----------------------------|------------------------------------|
  | 4-agent sequential pipeline | GPT-4o + Claude API (configurable) |
  | Claims automation           | FNOL extraction + fraud detection  |
  | No OCR                      | Vet invoice OCR                    |

  3. Integration

  | PetInsure360        | EIS-Dynamics POC                      |
  |---------------------|---------------------------------------|
  | Standalone platform | EIS ↔ Dynamics 365 bidirectional sync |
  | Direct ADLS writes  | Mock EIS APIs + Dataverse sync        |
  | No CRM integration  | Power Platform ready                  |

  4. Infrastructure Maturity

  | PetInsure360   | EIS-Dynamics POC               |
  |----------------|--------------------------------|
  | Single main.tf | Modular Terraform (10 modules) |
  | No CI/CD       | GitHub workflows ready         |
  | No tests       | pytest + e2e tests             |

  ---
  What PetInsure360 Has That EIS-Dynamics Doesn't

  - Medallion Lakehouse (Bronze/Silver/Gold layers)
  - Customer-facing portal (policy purchase, claim submission)
  - BI Dashboard with executive KPIs
  - CDP (Customer 360) with segmentation & cross-sell
  - Power BI integration (Synapse external tables)
  - Risk scoring tables

  What EIS-Dynamics Has That PetInsure360 Doesn't

  - Microservices architecture (separate deployable units)
  - Azure Service Bus (event-driven messaging)
  - Azure API Management (gateway with rate limiting)
  - Cosmos DB (NoSQL for operational data)
  - Dataverse/D365 integration (CRM-ready)
  - OCR for vet invoices (Document Intelligence)
  - Configurable AI providers (Claude/OpenAI/Azure OpenAI)
  - Test suite (unit + e2e tests)
  - Rating engine with breed/species factors

  ---
  Recommendation

  These projects are complementary, not competing:

  - PetInsure360 = Downstream analytics & data platform
  - EIS-Dynamics POC = Upstream operational system

  A complete solution would have EIS-Dynamics handling real-time claims → syncing to PetInsure360's lakehouse for analytics.


PetInsure360 Azure Deployment Details

  Found in terraform state (infra/terraform.tfstate) and backend/.env:

  Deployed Azure Resources

  | Resource                    | Name                    | Endpoint/URL                                       |
  |-----------------------------|-------------------------|----------------------------------------------------|
  | Storage Account (ADLS Gen2) | petinsud7i43            | https://petinsud7i43.dfs.core.windows.net/         |
  | Databricks Workspace        | petinsure360-databricks | https://adb-7405619408519767.7.azuredatabricks.net |
  | Synapse Serverless SQL      | petins-syn-ud7i43       | petins-syn-ud7i43-ondemand.sql.azuresynapse.net    |
  | Key Vault                   | petins-kv-ud7i43        | https://petins-kv-ud7i43.vault.azure.net/          |
  | Data Factory                | petinsure360-adf        | -                                                  |

  Storage Containers

  | Container | Purpose                     |
  |-----------|-----------------------------|
  | raw       | Raw JSON/CSV data ingestion |
  | bronze    | Delta Lake bronze layer     |
  | silver    | Delta Lake silver layer     |
  | gold      | Delta Lake gold layer       |

  Local Development URLs

  | Service         | URL                   |
  |-----------------|-----------------------|
  | Backend API     | http://localhost:8000 |
  | Frontend Portal | http://localhost:3000 |
  | BI Dashboard    | http://localhost:3001 |

  Configuration Files

  - Backend .env: /petinsure360/backend/.env - Contains storage account name and key
  - Terraform state: /petinsure360/infra/terraform.tfstate - All deployed resource details
  - Setup guide: /petinsure360/docs/SETUP_GUIDE.md - Step-by-step instructions
  
  