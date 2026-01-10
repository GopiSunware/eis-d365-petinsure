# MS Dynamics - Pet Insurance Platform

Enterprise insurance platform with AI-powered claims processing.

**Status:** ✅ **DEPLOYED** - Hybrid AWS (Compute) + Azure (Data Platform)

---

## 🚀 Live Deployment

### AWS Services (Compute Layer)

| Service | Production URL |
|---------|----------------|
| Customer Portal | http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com |
| BI Dashboard | http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com |
| EIS Agent Portal | http://eis-agent-portal.s3-website-us-east-1.amazonaws.com |
| EIS Admin Portal | http://eis-admin-portal.s3-website-us-east-1.amazonaws.com |
| Claims Data API | https://9wvcjmrknc.us-east-1.awsapprunner.com |
| Agent Pipeline | https://qi2p3x5gsm.us-east-1.awsapprunner.com |
| PetInsure360 Backend | https://fucf3fwwwv.us-east-1.awsapprunner.com |
| WebSocket (Real-time) | wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod |

### Azure Services (Data Platform)

| Service | Resource |
|---------|----------|
| Storage (ADLS Gen2) | petinsud7i43 |
| Databricks | petinsure360-databricks-dev |
| Key Vault | petins-kv-ud7i43 |

### Deployment Scripts

```bash
./scripts/validate-deployment.sh  # Pre-deployment validation (run first!)
./deploy-aws.sh                   # Deploy all services to AWS
./deploy-aws.sh status            # Check deployment status
./destroy-aws.sh                  # Clean up all AWS resources
./destroy-aws.sh --dry-run        # Preview what would be deleted
```

**Before deploying:** Run validation to catch common issues:
```bash
./scripts/validate-deployment.sh
```

See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for known issues and [AWS_DEPLOYMENT_FINAL_STATUS.md](AWS_DEPLOYMENT_FINAL_STATUS.md) for complete deployment details.

---

## ⚠️ CRITICAL RULES - READ FIRST

**Before writing ANY code:** Read [`CRITICAL_RULES.md`](CRITICAL_RULES.md)

### 🚫 NEVER USE SYSTEM /tmp/

```python
# ❌ WRONG - Will break in production
STATE_FILE = "/tmp/data.json"

# ✅ CORRECT - Use project paths
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = BASE_DIR / "data" / "state.json"
```

**Why:** System `/tmp` is ephemeral, not portable, and causes data loss.

---

## Quick Start (Local Development)

```bash
# Start all services locally
./start-demo.sh

# Or individual services (see PORT_CONFIG.md)
```

## Documentation

| File | Purpose |
|------|---------|
| **[CRITICAL_RULES.md](CRITICAL_RULES.md)** | 🚫 Never use /tmp - MUST READ |
| **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** | Pre-deployment validation & known issues |
| [AWS_DEPLOYMENT_FINAL_STATUS.md](AWS_DEPLOYMENT_FINAL_STATUS.md) | Current AWS deployment status |
| [CLAUDE.md](CLAUDE.md) | Claude Code configuration & skills |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture & tech stack |
| [ENV_VARIABLES.md](ENV_VARIABLES.md) | Environment variable reference |
| [PORT_CONFIG.md](PORT_CONFIG.md) | Service ports & URLs |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues & fixes |

## Project Structure

```
ms-dynamics/
├── eis-dynamics-poc/           # AI-powered claims processing
│   ├── src/ws4_agent_portal/   # Next.js frontend (3000)
│   ├── src/ws6_agent_pipeline/ # LangGraph agents (8006)
│   ├── src/ws7_docgen/        # Document AI (8007)
│   │   └── data/              # ✅ Project data (NOT /tmp)
│   └── src/shared/claims_data_api/ # Unified API (8000)
│
└── petinsure360/              # Azure data platform
    ├── frontend/              # Customer portal (3000)
    ├── bi-dashboard/          # Analytics dashboard (3001)
    ├── backend/               # FastAPI backend (3002)
    │   └── data/              # ✅ Project data (NOT /tmp)
    └── databricks/            # PySpark ETL

```

## Tech Stack

- **Frontend**: Next.js, React + Vite, TailwindCSS
- **Backend**: FastAPI, LangGraph, Socket.IO
- **AI**: OpenAI GPT-4o, Anthropic Claude
- **Data**: Azure Databricks, Delta Lake, ADLS Gen2
- **Storage**: Project-relative paths (see DATA_STORAGE.md)

## Services

| Port | Service | Description |
|------|---------|-------------|
| 3000 | Customer Portal | Customer-facing portal |
| 3001 | BI Dashboard | Executive analytics |
| 3002 | PetInsure360 Backend | FastAPI + Socket.IO |
| 8000 | **Claims Data API** | **Unified API Gateway** (20+ routers) |
| 8006 | Agent Pipeline | LangGraph claims agents |
| 8007 | DocGen | Document AI service |
| 8080 | Agent Portal | React Flow visualization |
| 8081 | EIS Admin Portal | Admin dashboard |

### Claims Data API Endpoints (Port 8000)

The unified API includes:
- `/api/v1/config/*` - Admin configuration (AI, claims, policies, rating)
- `/api/v1/approvals/*` - Approval workflows (stats, pending, actions)
- `/api/v1/audit/*` - Audit logging (events, timeline, compliance)
- `/api/v1/costs/*` - Cost monitoring (AWS, Azure, AI usage)
- `/api/chat/*` - AI chat interface
- `/api/pipeline/*` - Pipeline management
- Plus 15+ more service routers

See [PORT_CONFIG.md](PORT_CONFIG.md) and [ARCHITECTURE.md](ARCHITECTURE.md) for details.

## Data Storage ⚠️

**CRITICAL:** All data stored in project folders, NOT in `/tmp/`

```
✅ eis-dynamics-poc/src/ws7_docgen/data/
✅ petinsure360/backend/data/

❌ /tmp/                    # NEVER USE THIS
```

See [DATA_STORAGE.md](DATA_STORAGE.md) and [CRITICAL_RULES.md](CRITICAL_RULES.md).

## Development

### Environment Setup

```bash
# Backend services
cd eis-dynamics-poc/src/ws7_docgen
python -m uvicorn app.main:app --port 8007

# Frontend
cd petinsure360/frontend
npm run dev
```

### Key Configuration

- AI providers in `.env` files
- Service URLs in environment variables
- Data paths use `pathlib.Path` with project-relative paths

### Claude Code Skills

Available skills in `.claude/skills/`:
- `/claims-processing` - Claims processing workflows
- `/frontend-design` - UI/UX design patterns
- `/deploy-aws` - AWS deployment
- `/deploy-azure` - Azure deployment
- `/troubleshoot` - Debug issues

Use: `@skills/claims-processing` or just ask "use the claims-processing skill"

## Hybrid Cloud Architecture

**Current Setup:** AWS (Compute) + Azure (Data Platform)

### AWS (Compute Layer)
- 3 App Runner services (APIs)
- 4 S3 static websites (Frontends)
- Lambda + API Gateway (WebSocket)
- ECR (Container registry)

### Azure (Data Platform)
- ADLS Gen2 storage (Bronze/Silver/Gold medallion layers)
- Databricks workspace (PySpark ETL notebooks)
- Key Vault (Secrets management)

### Cost Estimate
- AWS: ~$79/month
- Azure: ~$20-25/month (data platform)
- **Total: ~$100-104/month**

---

**Remember:** Read [CRITICAL_RULES.md](CRITICAL_RULES.md) before coding!
