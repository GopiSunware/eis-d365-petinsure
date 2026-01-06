# Infrastructure Architecture

## Multi-Cloud Deployment

The EIS-Dynamics POC uses a multi-cloud architecture with AWS as the primary production environment and Azure for optional enterprise services.

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              PRODUCTION INFRASTRUCTURE                                     │
│                                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                         AWS (US-EAST-1) - PRIMARY                                    │  │
│  │                                                                                       │  │
│  │  ┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐   │  │
│  │  │        AWS AppRunner                │  │        AWS AppRunner                │   │  │
│  │  │   Claims Data API (Port 8000)       │  │   Agent Pipeline (Port 8006)        │   │  │
│  │  │                                     │  │                                     │   │  │
│  │  │  URL: p7qrmgi9sp.us-east-1          │  │  URL: bn9ymuxtwp.us-east-1          │   │  │
│  │  │       .awsapprunner.com             │  │       .awsapprunner.com             │   │  │
│  │  │                                     │  │                                     │   │  │
│  │  │  • 60+ REST Endpoints               │  │  • LangGraph Agent Pipeline         │   │  │
│  │  │  • 44 LLM Tools                     │  │  • WebSocket Events                 │   │  │
│  │  │  • CORS Enabled                     │  │  • Medallion Architecture           │   │  │
│  │  └─────────────────────────────────────┘  └─────────────────────────────────────┘   │  │
│  │                                                                                       │  │
│  │  ┌─────────────────────────────────────┐                                             │  │
│  │  │        AWS S3 (Optional)            │  Configuration:                             │  │
│  │  │  Delta Lake Storage                 │  • Auto-scaling enabled                     │  │
│  │  │  • Bronze layer                     │  • Health checks configured                 │  │
│  │  │  • Silver layer                     │  • Environment variables via AWS Secrets    │  │
│  │  │  • Gold layer                       │                                             │  │
│  │  └─────────────────────────────────────┘                                             │  │
│  └─────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                     AZURE (EAST US) - OPTIONAL ENTERPRISE                            │  │
│  │                                                                                       │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐                   │  │
│  │  │    Key Vault     │  │  Cosmos DB       │  │  Blob Storage    │                   │  │
│  │  │  kv-eisd365-dev  │  │ cosmos-eisd365   │  │  steisd365dev    │                   │  │
│  │  │                  │  │                  │  │                  │                   │  │
│  │  │  • API Keys      │  │  • sync_state    │  │  • vet-invoices  │                   │  │
│  │  │  • Conn Strings  │  │  • audit_logs    │  │  • med-records   │                   │  │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘                   │  │
│  │                                                                                       │  │
│  │  ┌──────────────────┐  ┌──────────────────┐                                         │  │
│  │  │   Service Bus    │  │   Dataverse      │                                         │  │
│  │  │  sb-eisd365-dev  │  │   (D365 CRM)     │                                         │  │
│  │  │                  │  │                  │                                         │  │
│  │  │  • policy-sync   │  │  • eis_policy    │                                         │  │
│  │  │  • claim-sync    │  │  • eis_pet       │                                         │  │
│  │  │  • claim-events  │  │  • eis_claim     │                                         │  │
│  │  └──────────────────┘  └──────────────────┘                                         │  │
│  └─────────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

## Local Development Environment

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              LOCAL DEVELOPMENT SERVICES                                    │
│                                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐  │
│  │  FRONTEND APPLICATIONS                                                               │  │
│  │  ┌──────────────────────────────┐    ┌──────────────────────────────┐               │  │
│  │  │  WS4: Agent Portal (:8080)   │    │  WS8: Admin Portal (:8081)   │               │  │
│  │  │  Next.js 14 + React 18       │    │  Next.js 14 + React 18       │               │  │
│  │  │  cd src/ws4_agent_portal     │    │  cd src/ws8_admin_portal/    │               │  │
│  │  │  npm run dev                 │    │  frontend && npm run dev     │               │  │
│  │  └──────────────────────────────┘    └──────────────────────────────┘               │  │
│  └─────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐  │
│  │  BACKEND SERVICES (FastAPI + Uvicorn)                                                │  │
│  │                                                                                       │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │  │
│  │  │ Claims API  │ │  WS2 AI     │ │ WS3 Integ   │ │ WS5 Rating  │ │ WS6 Pipeline│   │  │
│  │  │  :8000      │ │  :8001      │ │  :8002      │ │  :8003      │ │  :8006      │   │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │  │
│  │  ┌─────────────┐ ┌─────────────┐                                                    │  │
│  │  │ WS7 DocGen  │ │ WS8 Admin   │                                                    │  │
│  │  │  :8007      │ │  :8008      │                                                    │  │
│  │  └─────────────┘ └─────────────┘                                                    │  │
│  │                                                                                       │  │
│  │  Start command: uvicorn app.main:app --port {PORT} --reload                          │  │
│  └─────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐  │
│  │  DATA STORAGE (Local)                                                                │  │
│  │  ┌──────────────────────────────────────────────────────────────────────────────┐   │  │
│  │  │  src/shared/claims_data_api/app/data/                                         │   │  │
│  │  │  ├── customers.csv      (100 customers)                                       │   │  │
│  │  │  ├── pets.csv           (150 pets)                                            │   │  │
│  │  │  ├── policies.csv       (policies data)                                       │   │  │
│  │  │  ├── claims.jsonl       (438 claims)                                          │   │  │
│  │  │  ├── providers.csv      (51 vet providers)                                    │   │  │
│  │  │  └── fraud_patterns.json (3 fraud patterns)                                   │   │  │
│  │  └──────────────────────────────────────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

## Terraform Module Structure

```
infrastructure/
├── environments/
│   ├── dev/
│   │   ├── main.tf           # Dev environment orchestration
│   │   ├── variables.tf      # Dev-specific variables
│   │   ├── outputs.tf        # Dev outputs
│   │   └── terraform.tfvars  # Dev values
│   ├── staging/
│   │   └── ...
│   └── prod/
│       └── ...
├── modules/
│   ├── resource-group/       # Azure Resource Group
│   ├── key-vault/            # Azure Key Vault
│   ├── storage-account/      # Azure Blob Storage
│   ├── cosmos-db/            # Azure Cosmos DB
│   ├── service-bus/          # Azure Service Bus
│   ├── openai-service/       # Azure OpenAI
│   ├── apprunner/            # AWS AppRunner services
│   ├── ecr/                  # AWS ECR repositories
│   ├── s3/                   # AWS S3 buckets
│   └── iam/                  # AWS IAM roles & policies
└── scripts/
    ├── deploy-aws.sh         # AWS deployment script
    └── deploy-azure.sh       # Azure deployment script
```

## AWS Deployment (terraform/)

```
terraform/
├── deploy-aws.sh             # Main deployment script
├── main.tf                   # AWS provider & resources
├── variables.tf              # Input variables
├── outputs.tf                # Deployment outputs
└── apprunner.tf              # AppRunner service definitions
```

### AWS AppRunner Configuration

```hcl
# Claims Data API Service
resource "aws_apprunner_service" "claims_api" {
  service_name = "eis-claims-data-api"

  source_configuration {
    image_repository {
      image_identifier      = "ECR_IMAGE_URI"
      image_repository_type = "ECR"
    }
  }

  instance_configuration {
    cpu    = "1024"   # 1 vCPU
    memory = "2048"   # 2 GB RAM
  }

  health_check_configuration {
    protocol = "HTTP"
    path     = "/health"
  }
}

# Agent Pipeline Service
resource "aws_apprunner_service" "agent_pipeline" {
  service_name = "eis-agent-pipeline"

  instance_configuration {
    cpu    = "2048"   # 2 vCPU (for AI processing)
    memory = "4096"   # 4 GB RAM
  }
}
```

## Resource Naming Convention

```
Pattern: {resource-type}-{project}-{environment}-{region}

Examples:
├── rg-eis-d365-shared-dev-eastus     # Resource Group
├── kv-eisd365-dev                     # Key Vault (no hyphens)
├── steisd365dev                       # Storage (alphanumeric only)
├── cosmos-eisd365-dev                 # Cosmos DB
├── sb-eisd365-dev                     # Service Bus
├── oai-eisd365-dev                    # Azure OpenAI
└── apim-eisd365-dev                   # API Management
```

## Tagging Strategy

| Tag | Description | Example |
|-----|-------------|---------|
| `environment` | Deployment environment | `dev`, `staging`, `prod` |
| `project` | Project identifier | `eis-d365-poc` |
| `owner` | Team or individual | `insurance-platform` |
| `cost-center` | Billing allocation | `IT-12345` |
| `managed-by` | IaC tool | `terraform` |

## Secrets Management

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Azure Key Vault                              │
│                                                                      │
│  Secrets:                                                            │
│  ├── AZURE-OPENAI-KEY          # OpenAI API key                     │
│  ├── ANTHROPIC-API-KEY         # Claude API key                     │
│  ├── COSMOS-DB-KEY             # Cosmos primary key                 │
│  ├── SERVICE-BUS-CONN          # Service Bus connection string     │
│  ├── STORAGE-CONN              # Storage connection string          │
│  ├── DATAVERSE-CLIENT-SECRET   # D365 app registration secret      │
│  └── EIS-WEBHOOK-SECRET        # Webhook signature key             │
│                                                                      │
│  Access Policies:                                                    │
│  ├── WS2 Service (Managed Identity) → Get, List secrets            │
│  ├── WS3 Service (Managed Identity) → Get, List secrets            │
│  ├── WS5 Service (Managed Identity) → Get, List secrets            │
│  └── DevOps Pipeline (SPN) → Get, List, Set secrets                │
└─────────────────────────────────────────────────────────────────────┘
```

## Deployment Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                     GitHub Actions Workflow                          │
│                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │   Trigger   │───▶│    Build    │───▶│    Test     │             │
│  │  (PR/Push)  │    │   & Lint    │    │   (pytest)  │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│                                               │                      │
│                                               ▼                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    Environment Deployment                        ││
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         ││
│  │  │     Dev     │───▶│   Staging   │───▶│    Prod     │         ││
│  │  │  (auto)     │    │ (approval)  │    │ (approval)  │         ││
│  │  └─────────────┘    └─────────────┘    └─────────────┘         ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  Each environment:                                                   │
│  1. terraform init                                                   │
│  2. terraform plan                                                   │
│  3. terraform apply (with approval for staging/prod)                │
│  4. Deploy application containers                                    │
│  5. Run smoke tests                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Cost Estimation (Dev Environment)

| Resource | SKU | Monthly Est. |
|----------|-----|--------------|
| Azure OpenAI | GPT-4o (50K TPM) | $50-150 |
| Cosmos DB | Serverless | $10-30 |
| Service Bus | Standard | $10 |
| Storage Account | LRS | $5 |
| Key Vault | Standard | $3 |
| API Management | Consumption | $5-15 |
| Log Analytics | Pay-as-you-go | $5-10 |
| **Total** | | **~$90-225/mo** |

## Scaling Considerations

### Horizontal Scaling
- Container Apps: Auto-scale based on HTTP traffic
- Service Bus: Partitioned queues for throughput
- Cosmos DB: Serverless auto-scales to demand

### Vertical Scaling
- OpenAI: Increase TPM limits as needed
- APIM: Move to Standard tier for higher capacity

### Regional Expansion
- Cosmos DB: Add read replicas
- Service Bus: Geo-replication for DR
- Storage: RA-GRS for cross-region reads
