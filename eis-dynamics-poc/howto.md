# EIS-Dynamics POC - Quick Start Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI or Anthropic API key

---

## Setup (One Time)

```bash
# Navigate to project
cd "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install email-validator pydantic-settings

# Install shared module
cd src/shared && pip install -e .

# Install claims_data_api dependencies
cd claims_data_api && pip install -r requirements.txt && cd ..

# Install service dependencies
cd ../ws2_ai_claims && pip install -r requirements.txt
cd ../ws3_integration && pip install -r requirements.txt
cd ../ws5_rating_engine && pip install -r requirements.txt
cd ../ws6_agent_pipeline && pip install -r requirements.txt

# Return to project root
cd ../..

# Configure environment
cp .env.example .env
```

---

## Configure API Keys

Edit `.env` and add at least ONE API key:

```env
# Option A: OpenAI
OPENAI_API_KEY=sk-your-key-here

# Option B: Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Option C: Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

---

## Running Services

You need **6 terminals** running simultaneously:

### Terminal 1: Unified Claims API (Port 8000) - START FIRST
```bash
cd "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc"
source venv/bin/activate
cd src/shared/claims_data_api
uvicorn app.main:app --reload --port 8000
```

### Terminal 2: AI Claims (Port 8001)
```bash
cd "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc"
source venv/bin/activate
cd src/ws2_ai_claims
uvicorn app.main:app --reload --port 8001
```

### Terminal 3: Integration (Port 8002)
```bash
cd "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc"
source venv/bin/activate
cd src/ws3_integration
uvicorn app.main:app --reload --port 8002
```

### Terminal 4: Rating Engine (Port 8003)
```bash
cd "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc"
source venv/bin/activate
cd src/ws5_rating_engine
uvicorn app.main:app --reload --port 8003
```

### Terminal 5: Agent Portal (Port 3000)
```bash
cd "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc"
cd src/ws4_agent_portal
npm install  # First time only
npm run dev
```

### Terminal 6: Agent Pipeline (Port 8006)
```bash
cd "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc"
source venv/bin/activate
cd src/ws6_agent_pipeline
uvicorn app.main:app --reload --port 8006
```

---

## Access the Application

| Page | URL |
|------|-----|
| **Unified Claims API** | http://localhost:8000/docs |
| **Portal Home** | http://localhost:3000 |
| **Pipeline Dashboard** | http://localhost:3000/pipeline |
| **Code vs Agent Comparison** | http://localhost:3000/pipeline/compare |
| AI Claims API | http://localhost:8001/docs |
| Integration API | http://localhost:8002/docs |
| Rating API | http://localhost:8003/docs |
| **Agent Pipeline API** | http://localhost:8006/docs |

---

## Features

### 1. Pipeline Dashboard

The Agent Pipeline demonstrates AI-powered claims processing with 4 LangGraph agents:

1. Open http://localhost:3000/pipeline
2. Select mode: **Scenario** or **Demo**
3. Choose a scenario or complexity level
4. Click **Run Pipeline**
5. Watch real-time visualization:
   - Nodes animate as agents process
   - Reasoning panel shows agent thoughts
   - Edges show data flow

### 2. Code vs Agent Comparison

Compare deterministic code-driven processing against AI agent-driven processing:

1. Open http://localhost:3000/pipeline/compare
2. Select a scenario from the dropdown (20 pre-built scenarios)
3. Click **Run Comparison**
4. View side-by-side results:
   - Processing time comparison
   - Decision match/mismatch
   - Risk level assessment
   - Bronze/Silver/Gold layer outputs
   - AI insights (agent only)

### 3. AI-Powered Validation

ValidationService detects data quality issues rules cannot catch:

1. Open http://localhost:8000/docs
2. Navigate to **ValidationService** endpoints
3. Test validation scenarios:
   - `POST /api/v1/validation/run-scenario/VAL-001` (Diagnosis-Treatment mismatch)
   - `POST /api/v1/validation/run-scenario/VAL-007` (Expired license)
   - `POST /api/v1/validation/run-scenario/VAL-008` (Missing DEA)

---

## API Endpoints

### Unified Claims API (Port 8000)

```bash
# Health check
curl http://localhost:8000/

# Validation - Diagnosis-Treatment check
curl -X POST http://localhost:8000/api/v1/validation/diagnosis-treatment \
  -H "Content-Type: application/json" \
  -d '{"diagnosis_code":"S83.5","procedures":["Dental cleaning"]}'

# Validation - Run test scenario
curl -X POST http://localhost:8000/api/v1/validation/run-scenario/VAL-001

# Fraud detection
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"CUST-023","pet_id":"PET-034","provider_id":"PROV-011","claim_amount":1600,"diagnosis_code":"S83.5","service_date":"2024-12-15"}'

# Claims search
curl "http://localhost:8000/api/v1/claims/search?policy_id=POL-001"
```

### Scenarios API (Port 8006)
```bash
# List all scenarios
curl http://localhost:8006/api/v1/scenarios/

# Get specific scenario
curl http://localhost:8006/api/v1/scenarios/SCN-001

# Get scenarios by complexity
curl http://localhost:8006/api/v1/scenarios/complexity/simple
```

### Comparison API (Port 8006)
```bash
# Run quick comparison
curl -X POST "http://localhost:8006/api/v1/compare/quick?complexity=medium"

# Run scenario comparison
curl -X POST "http://localhost:8006/api/v1/compare/scenario/SCN-001"
```

### Pipeline API (Port 8006)
```bash
# Trigger demo pipeline
curl -X POST "http://localhost:8006/api/v1/pipeline/demo/claim?complexity=simple"

# Check pipeline run status
curl "http://localhost:8006/api/v1/pipeline/run/{run_id}"
```

---

## Troubleshooting

### "No module named 'eis_common'"
```bash
cd src/shared && pip install -e .
```

### "No module named 'email_validator'"
```bash
pip install email-validator pydantic-settings
```

### "No module named 'langchain_anthropic'"
```bash
pip install langchain-anthropic langchain-openai langgraph
```

### Port already in use
```bash
pkill -f "uvicorn.*8001"  # Replace 8001 with the port number
```

### Comparison takes too long
Agent processing can take 30-120 seconds depending on AI provider and claim complexity. Code-driven processing completes in < 1ms.

---

## Service Architecture

```
+----------------------------------------------------------------------+
|                    Agent Portal (Next.js :3000)                       |
|  +-------------+  +-------------+  +-----------------------------+   |
|  |   Claims    |  |  Policies   |  |  Pipeline Dashboard         |   |
|  |   Pages     |  |   Pages     |  |  - React Flow Visualization |   |
|  +------+------+  +------+------+  |  - Code vs Agent Compare    |   |
|         |                |         +-------------+---------------+   |
+---------+----------------+-----------------------+-----------------+
          |                |                       |
          v                v                       v
+--------------------+ +-----------------+ +---------------------------+
| Unified API :8000  | | Integration:8002| | Agent Pipeline :8006      |
| - 54 Endpoints     | | - EIS Mock APIs | | - Router Agent            |
| - 6 Services       | | - Data Sync     | | - Bronze/Silver/Gold      |
| - 44 LLM Tools     | +-----------------+ | - LangGraph Orchestrator  |
| - Validation       |                     | - 20 Demo Scenarios       |
+--------------------+                     +---------------------------+
          |
          v
+-----------------+ +---------------------------------------------------+
| AI Claims :8001 | |                   Rating Engine :8003             |
| - FNOL Extract  | |                   - Premium Calculation           |
| - Fraud Detect  | +---------------------------------------------------+
+-----------------+
```

---

## Project Structure

```
eis-dynamics-poc/
├── src/
│   ├── shared/               # Shared Library
│   │   └── claims_data_api/  # Unified API (Port 8000)
│   │       ├── app/
│   │       │   ├── services/     # 6 services (54 endpoints)
│   │       │   │   ├── claim_service.py
│   │       │   │   ├── policy_service.py
│   │       │   │   ├── pet_service.py
│   │       │   │   ├── provider_service.py
│   │       │   │   ├── medical_codes_service.py
│   │       │   │   └── validation_service.py
│   │       │   └── main.py
│   │       └── data/             # JSON data files
│   ├── ws2_ai_claims/        # AI Claims Service (Port 8001)
│   ├── ws3_integration/      # EIS Integration (Port 8002)
│   ├── ws4_agent_portal/     # Next.js Frontend (Port 3000)
│   │   ├── app/
│   │   │   └── pipeline/
│   │   │       ├── page.tsx      # Pipeline Dashboard
│   │   │       └── compare/
│   │   │           └── page.tsx  # Code vs Agent Comparison
│   │   └── lib/
│   │       └── pipeline-api.ts   # API Client
│   ├── ws5_rating_engine/    # Rating Engine (Port 8003)
│   └── ws6_agent_pipeline/   # Agent Pipeline (Port 8006)
│       ├── app/
│       │   ├── agents/           # LangGraph Agents
│       │   ├── routers/
│       │   │   ├── pipeline.py   # Pipeline API
│       │   │   ├── scenarios.py  # Scenarios API
│       │   │   └── comparison.py # Comparison API
│       │   ├── services/
│       │   │   └── code_processor.py  # Code-Driven Processor
│       │   └── tools/
│       │       └── unified_api_tools.py  # 44 LLM Tools
│       └── data/
│           └── claim_scenarios.json   # 20 Demo Scenarios
├── docs/                     # Documentation
├── howto.md                  # This file
└── .env                      # Environment config
```

---

## Version

**v0.9.0** - December 31, 2024

- ValidationService with 5 AI-powered validation types
- 54 API endpoints across 6 services
- 44 LLM tools for agent pipeline
- 10 validation test scenarios
- 3 fraud patterns for AI detection demo
- Provider licensing data (DEA, state licenses)

 Documentation Update Complete

  All documentation has been updated to v0.9.0. Here's a summary:

  Files Updated

  | File                               | Changes                                                    |
  |------------------------------------|------------------------------------------------------------|
  | docs/README.md                     | Updated to 54 endpoints, 44 tools, added ValidationService |
  | docs/technical/README.md           | Added validation endpoints, updated tool categories        |
  | howto.md                           | Added Terminal 1 for Unified API, validation examples      |
  | docs/SESSION_SUMMARY_2024-12-30.md | Consolidated from 8 sessions to concise summary            |

  Current State (v0.9.0)

  | Component            | Count                             |
  |----------------------|-----------------------------------|
  | API Endpoints        | 54 (across 6 services)            |
  | LLM Tools            | 44 (including 6 validation tools) |
  | Fraud Patterns       | 3 (AI vs Rules demo)              |
  | Validation Scenarios | 10                                |
  | Providers            | 51 (with licensing/DEA data)      |

  Key Features Added

  1. ValidationService - 5 AI-powered validation categories:
    - Diagnosis-Treatment Mismatch
    - Document Inconsistency
    - Claim Completeness/Sequence
    - License Verification
    - Controlled Substance Compliance
  2. 6 New LLM Tools for Gold agent validation
  3. 10 Test Scenarios (VAL-001 through VAL-010)

  Documentation Locations

  | Document                           | Purpose             |
  |------------------------------------|---------------------|
  | howto.md                           | Quick start guide   |
  | docs/README.md                     | Project overview    |
  | docs/technical/README.md           | Technical reference |
  | docs/SESSION_SUMMARY_2024-12-30.md | Build summary       |

