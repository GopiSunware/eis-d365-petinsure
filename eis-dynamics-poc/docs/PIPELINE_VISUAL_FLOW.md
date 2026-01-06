# Agent Pipeline Visual Flow UI

## Complete Documentation

---

## Overview

The Visual Flow UI provides a real-time visualization of the agent-driven medallion architecture. It shows claims processing through 4 LLM-powered agents (Router → Bronze → Silver → Gold) with live updates via WebSocket.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           VISUAL FLOW UI (Next.js)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   /pipeline     │    │ /pipeline/[id]  │    │ /pipeline/compare│         │
│  │   Dashboard     │    │   Run Detail    │    │  Code vs Agent  │         │
│  └────────┬────────┘    └────────┬────────┘    └─────────────────┘         │
│           │                      │                                          │
│  ┌────────┴──────────────────────┴────────────────────────────────┐        │
│  │                       Components                                │        │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │        │
│  │  │PipelineCanvas│  │  AgentNode   │  │ReasoningPanel│          │        │
│  │  │ (React Flow) │  │ (Custom Node)│  │ (Live Stream)│          │        │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │        │
│  │  ┌──────────────┐                                               │        │
│  │  │ MetricsCard  │                                               │        │
│  │  │ (Stats)      │                                               │        │
│  │  └──────────────┘                                               │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │                        Lib (Clients)                            │        │
│  │  ┌──────────────────┐      ┌──────────────────┐                 │        │
│  │  │  pipeline-api.ts │      │pipeline-websocket│                 │        │
│  │  │   (REST Client)  │      │  (WS Client)     │                 │        │
│  │  └────────┬─────────┘      └────────┬─────────┘                 │        │
│  └───────────┼─────────────────────────┼───────────────────────────┘        │
│              │                         │                                    │
└──────────────┼─────────────────────────┼────────────────────────────────────┘
               │                         │
               ▼                         ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    ws6_agent_pipeline (FastAPI + LangGraph)                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   REST API (:8006)                    WebSocket (:8006)                      │
│   ├─ POST /api/v1/pipeline/trigger    ├─ /ws/events (all events)            │
│   ├─ POST /api/v1/pipeline/demo/claim ├─ /ws/run/{id} (run events)          │
│   ├─ GET  /api/v1/pipeline/run/{id}   │                                     │
│   ├─ GET  /api/v1/pipeline/recent     │                                     │
│   └─ GET  /metrics                    │                                     │
│                                                                              │
│   ┌──────────────────────────────────────────────────────────────────┐      │
│   │                    LangGraph Pipeline                            │      │
│   │                                                                  │      │
│   │   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐             │      │
│   │   │ Router │──▶│ Bronze │──▶│ Silver │──▶│  Gold  │             │      │
│   │   │ Agent  │   │ Agent  │   │ Agent  │   │ Agent  │             │      │
│   │   └────────┘   └────────┘   └────────┘   └────────┘             │      │
│   │       │            │            │            │                   │      │
│   │       ▼            ▼            ▼            ▼                   │      │
│   │   Classify     Validate     Enrich      Risk Assess             │      │
│   │   Complexity   Clean        Normalize   Generate Insights       │      │
│   │                Detect       Apply Rules Final Decision          │      │
│   │                Anomalies                                        │      │
│   └──────────────────────────────────────────────────────────────────┘      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
src/ws4_agent_portal/
├── app/
│   └── pipeline/
│       ├── page.tsx                    # Main dashboard
│       ├── [id]/
│       │   └── page.tsx                # Run detail view
│       └── compare/
│           └── page.tsx                # Code vs Agent comparison
├── components/
│   └── pipeline/
│       ├── index.ts                    # Exports
│       ├── PipelineCanvas.tsx          # React Flow visualization
│       ├── AgentNode.tsx               # Custom agent nodes
│       ├── ReasoningPanel.tsx          # Live reasoning stream
│       └── MetricsCard.tsx             # Statistics display
└── lib/
    ├── pipeline-api.ts                 # REST API client
    └── pipeline-websocket.ts           # WebSocket client
```

---

## Pages

### 1. Dashboard (`/pipeline`)

**Features:**
- Metrics display (total runs, completed, failed, avg time)
- Complexity selector (Simple/Medium/Complex)
- Run Pipeline button
- Real-time React Flow canvas
- Reasoning panel with live agent thoughts
- Recent runs list with quick access

**Data Flow:**
1. Page mounts → Connects WebSocket → Loads recent runs + metrics
2. User clicks "Run Pipeline" → API call → Receives run_id
3. Polling starts (2s intervals) → Updates node states
4. WebSocket receives events → Updates reasoning panel
5. Pipeline completes → Stops polling → Refreshes recent runs

### 2. Run Detail (`/pipeline/[id]`)

**Features:**
- Run summary (claim ID, complexity, stage, time)
- Expandable agent output sections
- JSON-formatted agent responses
- Raw pipeline data view
- Copy run ID functionality

**Agent Sections:**
| Agent | Color | Shows |
|-------|-------|-------|
| Router | Blue | Complexity classification |
| Bronze | Orange | Validation decision, quality score |
| Silver | Gray | Enrichment status |
| Gold | Yellow | Final decision, risk level |

### 3. Comparison (`/pipeline/compare`)

**Features:**
- Side-by-side processing flow diagrams
- Scenario selector (Simple/Complex/Fraud)
- Results comparison (time, decision, confidence)
- Feature comparison table (8 aspects)
- Recommendation section

---

## Components

### PipelineCanvas

```typescript
interface PipelineCanvasProps {
  pipelineRun?: PipelineRun | null;
  onNodeClick?: (agentType: string) => void;
}
```

- Uses `@xyflow/react` for visualization
- 4 agent nodes with fixed positions
- Animated edges show current processing stage
- MiniMap and Controls included

### AgentNode

```typescript
interface AgentNodeData {
  label: string;
  agentType: "router" | "bronze" | "silver" | "gold";
  status: AgentStatus;  // pending | running | completed | failed
  processingTime?: number;
  decision?: string;
  confidence?: number;
  qualityScore?: number;
  riskLevel?: string;
  complexity?: string;
}
```

- Custom React Flow node
- Color-coded by agent type
- Status indicators with animations
- Shows relevant data per agent type

### ReasoningPanel

```typescript
interface ReasoningEntry {
  id: string;
  timestamp: string;
  agentName: string;
  type: "analysis" | "decision" | "observation" | "action" | "alert";
  content: string;
}
```

- Auto-scrolling live stream
- Color-coded entry types
- Expandable/collapsible
- Agent name badges

### MetricsCard

```typescript
interface PipelineMetrics {
  total_runs: number;
  active_runs: number;
  completed_runs: number;
  failed_runs: number;
  average_processing_time_ms: number;
}
```

- 4-column grid display
- Icon + color per metric type
- Loading skeleton support

---

## API Client

### pipelineApi

```typescript
// Singleton instance
import { pipelineApi } from "@/lib/pipeline-api";

// Methods
pipelineApi.health()                          // Health check
pipelineApi.triggerPipeline(request)          // Trigger async
pipelineApi.triggerDemoClaim(complexity)      // Demo claim
pipelineApi.getPipelineRun(runId)             // Get run status
pipelineApi.getRecentRuns(limit)              // Recent runs
pipelineApi.getMetrics()                      // Pipeline metrics
```

### pipelineWs

```typescript
// Singleton instance
import { pipelineWs } from "@/lib/pipeline-websocket";

// Connection
pipelineWs.connect()                          // Connect to /ws/events
pipelineWs.connectToRun(runId)                // Connect to /ws/run/{id}
pipelineWs.disconnect()                       // Close connection

// Event listeners
pipelineWs.on("*", callback)                  // All events
pipelineWs.on("reasoning", callback)          // Specific event
pipelineWs.onConnect(callback)                // Connection opened
pipelineWs.onDisconnect(callback)             // Connection closed
```

---

## Event Types

| Event | When | Data |
|-------|------|------|
| `pipeline.started` | Pipeline begins | run_id, claim_id |
| `agent.started` | Agent begins processing | agent_name, total_steps |
| `agent.completed` | Agent finishes | processing_time_ms, output_summary |
| `reasoning` | Agent thought | agent_name, reasoning_type, content |
| `decision` | Agent decision | decision_type, decision, confidence |
| `tool_call` | Tool invoked | tool_name, tool_input, tool_output |
| `pipeline.completed` | Pipeline finishes | total_time_ms, final_output |

---

## Styling

### Agent Colors

| Agent | Background | Border | Text |
|-------|------------|--------|------|
| Router | blue-50 | blue-200 | blue-700 |
| Bronze | orange-50 | orange-200 | orange-700 |
| Silver | gray-50 | gray-200 | gray-700 |
| Gold | yellow-50 | yellow-200 | yellow-700 |

### Status Icons

| Status | Icon | Color | Animation |
|--------|------|-------|-----------|
| Pending | Clock | gray-400 | none |
| Running | Loader2 | blue-500 | spin |
| Completed | CheckCircle | green-500 | none |
| Failed | XCircle | red-500 | none |

### CSS Animations

```css
/* Fade-in for reasoning entries */
@keyframes fade-in {
  0% { opacity: 0; transform: translateY(-10px); }
  100% { opacity: 1; transform: translateY(0); }
}

/* Pulse for active nodes */
@keyframes node-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.5); }
  50% { box-shadow: 0 0 0 8px rgba(59, 130, 246, 0); }
}
```

---

## How to Use

### 1. Start Services

```bash
# Terminal 1: Agent Pipeline
cd src/ws6_agent_pipeline
uvicorn app.main:app --reload --port 8006

# Terminal 2: Agent Portal
cd src/ws4_agent_portal
npm run dev
```

### 2. Access UI

| Page | URL |
|------|-----|
| Dashboard | http://localhost:3000/pipeline |
| Run Detail | http://localhost:3000/pipeline/{run_id} |
| Comparison | http://localhost:3000/pipeline/compare |

### 3. Run a Demo

1. Open http://localhost:3000/pipeline
2. Select complexity: Simple / Medium / Complex
3. Click "Run Pipeline"
4. Watch the visualization:
   - Nodes light up as agents process
   - Edges animate to show data flow
   - Reasoning panel shows live thoughts
5. Click "View Details" for full output

---

## Demo Scenarios

| Complexity | Claim Type | Amount | Expected Result |
|------------|------------|--------|-----------------|
| Simple | Wellness | $150 | AUTO_APPROVE, Low risk |
| Medium | Accident | $4,500 | STANDARD_REVIEW, Medium risk |
| Complex | Emergency | $12,500 | MANUAL_REVIEW, High risk |

---

## Dependencies

```json
{
  "@xyflow/react": "^12.x",
  "clsx": "^2.x",
  "lucide-react": "^0.x"
}
```

---

## Environment Variables

```env
# Optional - defaults to localhost:8006
NEXT_PUBLIC_PIPELINE_API_URL=http://localhost:8006
NEXT_PUBLIC_PIPELINE_WS_URL=ws://localhost:8006
```

---

## Troubleshooting

### WebSocket Not Connecting

1. Ensure ws6_agent_pipeline is running on port 8006
2. Check browser console for connection errors
3. Verify no CORS issues (pipeline service allows all origins)

### Pipeline Not Updating

1. Check if polling is active (2s intervals)
2. Verify run_id is valid
3. Check API responses in Network tab

### TypeScript Errors

```bash
cd src/ws4_agent_portal
npx tsc --noEmit
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-12-29 | Initial release - Phase 3 complete |
