# Claude Code Configuration

## ⚠️ CRITICAL: Read First

**Before writing ANY code, read:** [`CRITICAL_RULES.md`](CRITICAL_RULES.md)

**🚫 NEVER use system `/tmp/` folder** - Use project-relative paths only!

---

## Project Overview

This workspace contains two integrated pet insurance demo projects:

### 1. EIS-Dynamics POC (`eis-dynamics-poc/`)
AI-powered insurance claims processing with LangGraph agents.
- **Frontend**: Next.js (port 3000) with React Flow visualization
- **Backend**: FastAPI microservices (ports 8000-8006)
- **AI**: LangGraph agents for claims processing (Bronze/Silver/Gold layers)

### 2. PetInsure360 (`petinsure360/`)
Azure-based data platform with medallion lakehouse architecture.
- **Frontend**: React + Vite (port 3000) - Customer portal
- **BI Dashboard**: React (port 3001) - Executive analytics
- **Backend**: FastAPI + Socket.IO (port 3002)
- **Data**: Azure ADLS Gen2, Databricks, Delta Lake

## Skills

Available skills in `.claude/skills/`:

### `/frontend-design` - UI Aesthetics
Use when building or improving UI components. Covers typography, colors, animations, backgrounds, and dashboard patterns.

### `/claims-processing` - Claims Processing (Parent)
Master skill for pet insurance claims. Orchestrates rule-based and AI agent-driven approaches.

#### Child Skills:
| Skill | Use For |
|-------|---------|
| `/claims/submit` | Submit claims (Portal, API, Pipeline, Documents) |
| `/claims/validate` | 5 validation types (diagnosis mismatch, docs, license, DEA) |
| `/claims/fraud` | Fraud detection (chronic gaming, provider collusion, timing) |
| `/claims/docgen` | Document AI extraction & generation |
| `/claims/pipeline` | Agent pipeline (Router→Bronze→Silver→Gold) |
| `/claims/compare` | Rule-based vs Agent comparison |
| `/claims/scenarios` | 36 pre-built test scenarios |

### `/claude-code-features` - Claude Code Guide
Comprehensive guide for Claude Code extensibility features. Use when deciding:
- **Skills vs Sub-agents vs Hooks** - Which to use when
- **MCP** - How to connect external tools
- **Plugins** - How to distribute extensions
- **Headless Mode** - CI/CD integration
- **Output Styles** - Customizing Claude's behavior

**Quick Decision**:
| I want to... | Use |
|-------------|-----|
| Teach Claude domain knowledge | Skills |
| Delegate to specialized AI | Sub-agents |
| Auto-run scripts on events | Hooks |
| Connect to external APIs/DBs | MCP |
| Share tools with team | Plugins |
| Use Claude in CI/CD | Headless Mode |

**Activation**: Say "use the claude-code-features skill" or ask "how do I use skills/agents/hooks?"

### Additional Skills
| Skill | Use For |
|-------|---------|
| `/deploy-aws` | AWS deployment workflows |
| `/deploy-azure` | Azure deployment workflows |
| `/env-config` | Environment configuration management |
| `/troubleshoot` | Debugging and issue diagnosis |
| `/github` | GitHub workflows and PAT setup |

## Sub-Agents

Available agents in `.claude/agents/` - automatically invoked when context matches:

| Agent | Description | Skills Used |
|-------|-------------|-------------|
| `code-reviewer` | Reviews code for quality, security, best practices | - |
| `security-auditor` | Security vulnerability analysis (OWASP Top 10) | - |
| `frontend-designer` | UI/UX improvements using design system | frontend-design |
| `test-runner` | Run tests and fix failures | - |
| `debugger` | Systematic issue investigation | troubleshoot |
| `claims-analyst` | Claims processing domain expert | claims-processing |

**Usage**: Agents auto-activate, or say "use the code-reviewer agent" explicitly.

## Slash Commands

Quick actions in `.claude/commands/`:

| Command | Description |
|---------|-------------|
| `/review` | Code review current changes |
| `/test` | Run tests (optionally fix failures) |
| `/scenario` | Run claims test scenarios |
| `/debug` | Investigate and resolve issues |
| `/security` | Security audit the codebase |
| `/ui` | UI design improvements |

**Examples**:
```
/review staged        # Review staged changes
/test fix            # Run tests, fix failures
/scenario FRAUD-001  # Run fraud detection test
/security auth       # Audit authentication code
```

## Hooks (Automation)

Configured in `.claude/settings.json`:

| Event | Hook | Purpose |
|-------|------|---------|
| PreToolUse | File protection | Block edits to .env, secrets, credentials |
| PostToolUse | Auto-format | Format .ts/.tsx with Prettier, .py with Black |
| Stop | Session log | Log session completion |

## MCP Servers

External tool connections in `.mcp.json`:

**Active**:
- `github` - GitHub integration for PRs, issues, code

**Templates available** (copy to mcpServers and configure):
- `sentry-template` - Error monitoring
- `postgres-template` - PostgreSQL database
- `mongodb-template` - MongoDB database
- `slack-template` - Slack integration
- `linear-template` - Issue tracking
- `notion-template` - Documentation

**Add new server**:
```bash
claude mcp add --transport http NAME URL
```

## Tech Stack

| Layer | EIS-Dynamics | PetInsure360 |
|-------|--------------|--------------|
| Frontend | Next.js, React Flow, TailwindCSS | React, Vite, TailwindCSS |
| Backend | FastAPI, LangGraph | FastAPI, Socket.IO |
| AI | OpenAI, Anthropic Claude | Azure OpenAI |
| Storage | JSON files | Azure ADLS Gen2, Delta Lake |
| ETL | - | Azure Databricks (PySpark) |

## Key Directories

```
ms-dynamics/
├── .claude/
│   ├── agents/                      # Sub-agents
│   │   ├── code-reviewer.md
│   │   ├── security-auditor.md
│   │   ├── frontend-designer.md
│   │   ├── test-runner.md
│   │   ├── debugger.md
│   │   └── claims-analyst.md
│   ├── commands/                    # Slash commands
│   │   ├── review.md
│   │   ├── test.md
│   │   ├── scenario.md
│   │   ├── debug.md
│   │   ├── security.md
│   │   └── ui.md
│   ├── skills/                      # Skills
│   │   ├── frontend-design.md
│   │   ├── claims-processing.md
│   │   ├── claude-code-features.md
│   │   ├── claims/                  # Claims child skills
│   │   ├── deploy-aws/
│   │   ├── deploy-azure/
│   │   ├── env-config/
│   │   ├── troubleshoot/
│   │   └── github/
│   └── settings.json                # Hooks configuration
├── .mcp.json                        # MCP server connections
├── eis-dynamics-poc/
│   └── src/
│       ├── ws4_agent_portal/        # Next.js frontend (port 3000)
│       ├── ws6_agent_pipeline/      # LangGraph agents (port 8006)
│       ├── ws7_docgen/              # Document AI service (port 8007)
│       └── shared/claims_data_api/  # Unified API (port 8000)
└── petinsure360/
    ├── frontend/                    # React customer portal
    ├── bi-dashboard/                # BI analytics dashboard
    └── backend/                     # FastAPI + Socket.IO
```

## Running Services

### Quick Start (All Services)
```bash
./start-demo.sh
```

### Individual Services
See `ARCHITECTURE.md` for detailed port configuration.

### CRITICAL: Troubleshooting Reference
**Always check `TROUBLESHOOTING.md` for common issues:**
- WebSocket fails → Use `socket_app` not `app` for PetInsure360 backend
- CORS errors → EIS services need `["*"]` fallback for cors_origins
- Chat API 404 → Chat is on port **8000**, not 8003 or 8008
- Missing services → All 12 services must run (3 PetInsure + 7 EIS backend + 2 EIS frontend)

### Complete Port Reference
**PetInsure360:** 3000 (Portal), 3001 (BI), 3002 (Backend + Socket.IO)
**EIS Dynamics Backend:** 8000 (Claims API + Chat), 8002, 8003, 8005, 8006, 8007, 8008
**EIS Dynamics Frontend:** 8080 (Agent Portal), 8081 (Admin Portal)

## Coding Conventions

- **Python**: FastAPI, Pydantic models, async/await
- **TypeScript**: Strict mode, functional components
- **React**: Hooks, TailwindCSS for styling
- **CSS**: CSS variables for theming, mobile-first responsive
