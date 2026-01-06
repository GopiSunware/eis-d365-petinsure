# Getting Started

## Prerequisites

### Required Tools
- Python 3.11+
- Node.js 18+
- Git

### API Keys (at least one required)
- OpenAI API key, OR
- Anthropic API key, OR
- Azure OpenAI credentials

---

## Quick Setup

```bash
# Clone and navigate
git clone https://github.com/your-org/eis-dynamics-poc.git
cd eis-dynamics-poc

# Create Python environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install email-validator pydantic-settings
cd src/shared && pip install -e .
cd ../ws2_ai_claims && pip install -r requirements.txt
cd ../ws3_integration && pip install -r requirements.txt
cd ../ws5_rating_engine && pip install -r requirements.txt
cd ../ws6_agent_pipeline && pip install -r requirements.txt
cd ../..

# Configure environment
cp .env.example .env
# Edit .env and add your API key
```

---

## Environment Configuration

Create `.env` file in project root with at least ONE AI provider:

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

Open 5 terminal windows and run each service:

| Terminal | Service | Port | Command |
|----------|---------|------|---------|
| 1 | AI Claims | 8001 | `cd src/ws2_ai_claims && uvicorn app.main:app --reload --port 8001` |
| 2 | Integration | 8002 | `cd src/ws3_integration && uvicorn app.main:app --reload --port 8002` |
| 3 | Rating Engine | 8003 | `cd src/ws5_rating_engine && uvicorn app.main:app --reload --port 8003` |
| 4 | Agent Portal | 3000 | `cd src/ws4_agent_portal && npm run dev` |
| 5 | Agent Pipeline | 8006 | `cd src/ws6_agent_pipeline && uvicorn app.main:app --reload --port 8006` |

**Note:** Python services require `source venv/bin/activate` first.

---

## Verify Installation

```bash
# Check service health
curl http://localhost:8001/health  # AI Claims
curl http://localhost:8002/health  # Integration
curl http://localhost:8003/health  # Rating Engine
curl http://localhost:8006/health  # Agent Pipeline

# Test demo pipeline
curl -X POST "http://localhost:8006/api/v1/pipeline/demo/claim?complexity=simple"
```

---

## Project Structure

```
eis-dynamics-poc/
├── docs/                    # Documentation
│   ├── README.md            # Overview
│   ├── PIPELINE_VISUAL_FLOW.md  # Pipeline UI docs
│   ├── architecture/        # System design
│   ├── technical/           # Developer guides
│   ├── business-flows/      # Process docs
│   └── api/                 # API reference
├── src/
│   ├── shared/              # Shared Python library
│   │   └── eis_common/
│   ├── ws2_ai_claims/       # AI Claims (port 8001)
│   ├── ws3_integration/     # Integration (port 8002)
│   ├── ws4_agent_portal/    # Next.js Portal (port 3000)
│   │   ├── app/pipeline/    # Pipeline UI pages
│   │   └── components/pipeline/  # React Flow components
│   ├── ws5_rating_engine/   # Rating Engine (port 8003)
│   └── ws6_agent_pipeline/  # Agent Pipeline (port 8006)
│       ├── agents/          # LangGraph agents
│       ├── tools/           # Agent tools
│       └── orchestration/   # Pipeline logic
├── howto.md                 # Quick start guide
└── .env                     # Configuration
```

---

## Key URLs

| Page | URL |
|------|-----|
| Portal Home | http://localhost:3000 |
| Pipeline Dashboard | http://localhost:3000/pipeline |
| Pipeline Compare | http://localhost:3000/pipeline/compare |
| AI Claims Swagger | http://localhost:8001/docs |
| Integration Swagger | http://localhost:8002/docs |
| Rating Swagger | http://localhost:8003/docs |
| Agent Pipeline Swagger | http://localhost:8006/docs |

---

## IDE Setup (VS Code)

### Recommended Extensions
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Ruff (charliermarsh.ruff)
- Tailwind CSS (bradlc.vscode-tailwindcss)
- Prettier (esbenp.prettier-vscode)

### Workspace Settings
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true
}
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No module named 'eis_common'" | `cd src/shared && pip install -e .` |
| "No module named 'email_validator'" | `pip install email-validator pydantic-settings` |
| Port already in use | `pkill -f "uvicorn.*8001"` |
| WebSocket not connecting | Ensure port 8006 is running |
| Node modules issues | Delete `node_modules` and run `npm install` |

---

## Next Steps

1. Read [howto.md](../../howto.md) for complete setup
2. See [PIPELINE_VISUAL_FLOW.md](../PIPELINE_VISUAL_FLOW.md) for pipeline UI docs
3. Check [architecture/](../architecture/) for system design
4. Browse [api/](../api/) for API reference
