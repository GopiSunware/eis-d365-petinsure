# Port Configuration Reference

## Overview

This document is the **single source of truth** for all service ports across both projects.

---

## PetInsure360 (Ports 3000-3099)

| Component | Type | Port | URL | Path |
|-----------|------|------|-----|------|
| Customer Portal | UI (Vite/React) | **3000** | http://localhost:3000 | `petinsure360/frontend/` |
| BI Dashboard | UI (Vite/React) | **3001** | http://localhost:3001 | `petinsure360/bi-dashboard/` |
| Backend API | Service (FastAPI) | **3002** | http://localhost:3002/docs | `petinsure360/backend/` |

### How to Start PetInsure360

```bash
# Terminal 1: Backend API
cd petinsure360/backend
source env_backend/bin/activate
uvicorn app.main:socket_app --host 0.0.0.0 --port 3002 --reload

# Terminal 2: Customer Portal
cd petinsure360/frontend
npm run dev

# Terminal 3: BI Dashboard
cd petinsure360/bi-dashboard
npm run dev
```

---

## EIS Dynamics POC (Ports 8000-8099)

### Backend Services

| Service | Port | URL | Path |
|---------|------|-----|------|
| Claims Data API | **8000** | http://localhost:8000/docs | `eis-dynamics-poc/src/shared/claims_data_api/` |
| WS2 AI Claims | **8002** | http://localhost:8002/docs | `eis-dynamics-poc/src/ws2_ai_claims/` |
| WS3 Integration | **8003** | http://localhost:8003/docs | `eis-dynamics-poc/src/ws3_integration/` |
| WS5 Rating Engine | **8005** | http://localhost:8005/docs | `eis-dynamics-poc/src/ws5_rating_engine/` |
| WS6 Agent Pipeline | **8006** | http://localhost:8006/docs | `eis-dynamics-poc/src/ws6_agent_pipeline/` |
| WS7 DocGen | **8007** | http://localhost:8007/docs | `eis-dynamics-poc/src/ws7_docgen/` |
| WS8 Admin Backend | **8008** | http://localhost:8008/docs | `eis-dynamics-poc/src/ws8_admin_portal/backend/` |

### Frontend UIs

| UI | Port | URL | Path |
|----|------|-----|------|
| WS4 Agent Portal | **8080** | http://localhost:8080 | `eis-dynamics-poc/src/ws4_agent_portal/` |
| WS8 Admin Portal | **8081** | http://localhost:8081 | `eis-dynamics-poc/src/ws8_admin_portal/frontend/` |

### How to Start EIS Dynamics

```bash
# Terminal 1: Claims Data API (START FIRST)
cd eis-dynamics-poc/src/shared/claims_data_api
source ../../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: WS6 Agent Pipeline
cd eis-dynamics-poc/src/ws6_agent_pipeline
uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload

# Terminal 3: WS7 DocGen
cd eis-dynamics-poc/src/ws7_docgen
uvicorn app.main:app --host 0.0.0.0 --port 8007 --reload

# Terminal 4: WS8 Admin Backend
cd eis-dynamics-poc/src/ws8_admin_portal/backend
uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload

# Terminal 5: WS4 Agent Portal (UI)
cd eis-dynamics-poc/src/ws4_agent_portal
npm run dev

# Terminal 6: WS8 Admin Portal (UI)
cd eis-dynamics-poc/src/ws8_admin_portal/frontend
npm run dev
```

---

## Quick Reference

```
PETINSURE360                          EIS DYNAMICS
============                          ============
3000 - Customer Portal (UI)           8000 - Claims Data API
3001 - BI Dashboard (UI)              8002 - WS2 AI Claims
3002 - Backend API                    8003 - WS3 Integration
                                      8005 - WS5 Rating Engine
                                      8006 - WS6 Agent Pipeline
                                      8007 - WS7 DocGen
                                      8008 - WS8 Admin Backend
                                      8080 - WS4 Agent Portal (UI)
                                      8081 - WS8 Admin Portal (UI)
```

---

---

## Integration Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PETINSURE360                                   │
│                        (Rule-Based Processing)                           │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│  │ Customer Portal │───▶│   Backend API   │───▶│  BI Dashboard   │     │
│  │   (UI: 3000)    │    │    (3002)       │    │   (UI: 3001)    │     │
│  └─────────────────┘    └────────┬────────┘    └─────────────────┘     │
│                                  │                                       │
└──────────────────────────────────┼───────────────────────────────────────┘
                                   │
                                   │ Claims Upload
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           EIS DYNAMICS                                   │
│                        (Agent-Driven Processing)                         │
│                                                                          │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│  │   WS7 DocGen    │───▶│  WS6 Pipeline   │───▶│ WS8 Admin       │     │
│  │    (8007)       │    │    (8006)       │    │ Backend (8008)  │     │
│  │  AI Document    │    │  Agent Claims   │    │                 │     │
│  │  Processing     │    │  Processing     │    │                 │     │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘     │
│           │                                                              │
│           │                      ┌─────────────────┐                    │
│           └─────────────────────▶│ Claims Data API │                    │
│                                  │    (8000)       │                    │
│  ┌─────────────────┐             └─────────────────┘                    │
│  │ WS4 Agent Portal│                     ▲                              │
│  │   (UI: 8080)    │─────────────────────┘                              │
│  └─────────────────┘                                                     │
│                                                                          │
│  ┌─────────────────┐                                                     │
│  │ WS8 Admin Portal│                                                     │
│  │   (UI: 8081)    │                                                     │
│  └─────────────────┘                                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User uploads claim documents** via PetInsure360 Customer Portal (3000)
2. **PetInsure360 Backend (3002)** receives files and forwards to EIS DocGen
3. **WS7 DocGen (8007)** runs AI agent to:
   - Extract document data (OCR)
   - Validate against policy
   - Check for fraud/duplicates
   - Make decision (approve/review/reject)
4. **Results flow back** to PetInsure360 for display
5. **Agents can view/process** claims in EIS Agent Portal (8080)
6. **Admins can configure** rules in EIS Admin Portal (8081)

---

## Configuration Files Updated

### PetInsure360
- `petinsure360/frontend/vite.config.js` - port 3000, proxy to 3002
- `petinsure360/bi-dashboard/vite.config.js` - port 3001, proxy to 3002
- `petinsure360/backend/app/main.py` - port 3002

### EIS Dynamics
- `eis-dynamics-poc/src/.env` - all service URLs
- `eis-dynamics-poc/src/ws4_agent_portal/package.json` - port 8080
- `eis-dynamics-poc/src/ws4_agent_portal/.env.local` - service URLs
- `eis-dynamics-poc/src/ws8_admin_portal/backend/app/config.py` - port 8008
- `eis-dynamics-poc/src/ws8_admin_portal/frontend/package.json` - port 8081
- `eis-dynamics-poc/src/ws8_admin_portal/frontend/.env.local` - port 8081, API URL
- `eis-dynamics-poc/src/shared/claims_data_api/app/main.py` - CORS origins

---

## Important Notes

### WS3 Integration as Data Proxy
The `CLAIMS_DATA_API_URL` and `NEXT_PUBLIC_CLAIMS_API_URL` environment variables point to **WS3 Integration (8003)** rather than Claims Data API (8000). This is intentional:

- **WS3 Integration (8003)** acts as a proxy/mock for EIS systems
- It provides `/api/v1/eis/*` endpoints for policies, claims, customers
- WS7 DocGen and WS4 Agent Portal use WS3 for claims data

For direct database access, use:
- **Claims Data API (8000)** - Direct access to PolicyService, CustomerService, etc.

### PetInsure360 ↔ EIS Integration
- PetInsure360 Backend (3002) communicates with WS7 DocGen (8007) for document processing
- Environment variable: `DOCGEN_SERVICE_URL=http://localhost:8007`
- Real-time updates via Socket.IO from backend to frontend

### Environment Files Summary
| Service | .env Location | Key Variables |
|---------|---------------|---------------|
| PetInsure360 Backend | `petinsure360/backend/.env` | `API_PORT=3002`, `DOCGEN_SERVICE_URL` |
| EIS Services | `eis-dynamics-poc/src/.env` | All `WS*_URL` variables |
| WS4 Agent Portal | `eis-dynamics-poc/src/ws4_agent_portal/.env.local` | `NEXT_PUBLIC_*` frontend vars |
| WS8 Admin Frontend | `eis-dynamics-poc/src/ws8_admin_portal/frontend/.env.local` | `NEXT_PUBLIC_API_URL=http://localhost:8008` |
