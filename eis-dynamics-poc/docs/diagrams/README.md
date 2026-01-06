# EIS-Dynamics POC - Architecture Diagrams

## Quick Start - View Diagrams Now

### Mermaid (.mmd files) - Recommended
1. Go to **[mermaid.live](https://mermaid.live)**
2. Delete the default content
3. Copy/paste content from any `.mmd` file
4. Diagram renders instantly
5. Click **Actions → Download PNG**

### PlantUML (.puml files)
1. Go to **[plantuml.com/plantuml](https://www.plantuml.com/plantuml/uml/)**
2. Copy/paste content from any `.puml` file
3. Click **Submit**
4. Right-click image → Save As

---

## File List

| File | Format | Description |
|------|--------|-------------|
| `01-azure-architecture.mmd` | Mermaid | Full multi-cloud architecture (AWS primary, Azure optional) |
| `02-medallion-flow.mmd` | Mermaid | Pet insurance data flow: RAW → Bronze → Silver → Gold |
| `03-ai-pipeline.mmd` | Mermaid | LangGraph agent pipeline with Router/Bronze/Silver/Gold agents |
| `04-rule-vs-ai.mmd` | Mermaid | Rules vs AI comparison - key demo slide |
| `puml-01-architecture.puml` | PlantUML | Multi-cloud architecture |
| `puml-02-medallion.puml` | PlantUML | Medallion data layers |
| `puml-03-ai-pipeline.puml` | PlantUML | AI agent flow |
| `puml-04-comparison.puml` | PlantUML | Rules vs AI |

---

## Architecture Overview

### Services & Ports

| Service | Port | Technology |
|---------|------|------------|
| Claims Data API | :8000 | FastAPI (60+ endpoints, 44 LLM tools) |
| WS2: AI Claims | :8001 | FastAPI |
| WS3: Integration | :8002 | FastAPI |
| WS5: Rating Engine | :8003 | FastAPI |
| WS6: Agent Pipeline | :8006 | LangGraph |
| WS7: DocGen | :8007 | FastAPI |
| WS8: Admin API | :8008 | FastAPI |
| WS4: Agent Portal | :8080 | Next.js |
| WS8: Admin Portal | :8081 | Next.js |

### Live Deployments (AWS AppRunner)
- **Claims API**: `p7qrmgi9sp.us-east-1.awsapprunner.com`
- **Agent Pipeline**: `bn9ymuxtwp.us-east-1.awsapprunner.com`

---

## Diagram Descriptions

### 1. Multi-Cloud Architecture (`01-*.mmd`)
Shows all services and cloud deployment:
- Frontend → Gateway → Microservices → AI Processing
- AWS AppRunner (primary) with live services
- Azure (optional): Cosmos DB, Blob Storage, Service Bus
- AI Models: Claude Sonnet (primary), GPT-4o (fallback)
- D365 Dataverse integration

### 2. Medallion Data Flow (`02-*.mmd`)
Pet insurance data transformation:
- **RAW**: pet_owners, pets, policies, claims, providers (CSV/JSONL)
- **BRONZE**: Validated data (schema enforcement, field checks)
- **SILVER**: Enriched data (customer 360, medical history, coverage)
- **GOLD**: Decision output (claim decisions, fraud analytics, KPIs)

### 3. AI Agent Pipeline (`03-*.mmd`)
LangGraph processing flow:
- **Router Agent**: Classifies complexity (fast_track | standard | enhanced)
- **Bronze Agent**: Validates fields, policy status, waiting period
- **Silver Agent**: Enriches with pet owner 360, policy details, medical history
- **Gold Agent**: Calculates fraud score, checks pre-existing, generates decision

### 4. Rules vs AI Comparison (`04-*.mmd`)
**Key demo slide** - Same pet claim, different outcomes:
- **Rules Engine**: APPROVED in 0.5ms (misses fraud patterns)
- **AI Pipeline**: MANUAL REVIEW with 0.72 fraud score (catches patterns)

Demonstrates AI value: breed-prone conditions, claim frequency, provider rotation

---

## For Professional Presentations

### Option 1: Excalidraw (Free, Fast)
1. Go to [excalidraw.com](https://excalidraw.com)
2. Use shapes to recreate diagrams
3. Whiteboard style looks modern
4. Export as PNG

### Option 2: Draw.io with Azure/AWS Icons
1. Go to [app.diagrams.net](https://app.diagrams.net)
2. Click **+ More Shapes** → Enable **Azure** and **AWS**
3. Drag icons onto canvas
4. Export as PNG/SVG

### Option 3: PowerPoint
1. Download [Azure Icons](https://learn.microsoft.com/en-us/azure/architecture/icons/)
2. Download [AWS Icons](https://aws.amazon.com/architecture/icons/)
3. Insert icons in PowerPoint
4. Use included `EIS-Dynamics-Architecture.pptx` as template

---

## VS Code Extensions

For editing diagrams in VS Code:
- **Mermaid**: "Markdown Preview Mermaid Support"
- **PlantUML**: "PlantUML" (requires Java)
