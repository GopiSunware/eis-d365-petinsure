# PetInsure360 DocGen Integration - Session Summary
**Date:** January 4, 2026

## What Was Completed

### DocGen Integration into PetInsure360
Integrated the AI Document Processing (DocGen) feature from EIS Portal into the PetInsure360 ecosystem.

### Files Created/Modified

| File | Action | Description |
|------|--------|-------------|
| `petinsure360/backend/app/api/docgen.py` | Created | DocGen API routes for PetInsure360 backend |
| `petinsure360/backend/app/main.py` | Modified | Added docgen router registration |
| `petinsure360/frontend/src/pages/UploadDocsPage.jsx` | Created | Customer document upload page |
| `petinsure360/frontend/src/App.jsx` | Modified | Added Upload Documents nav/route + socket events |
| `petinsure360/bi-dashboard/src/pages/PipelinePage.jsx` | Modified | Renamed to "Legacy Pipeline (Rule-Based)" |
| `petinsure360/bi-dashboard/src/pages/AgentPipelinePage.jsx` | Created | AI Agent Pipeline view |
| `petinsure360/bi-dashboard/src/pages/DocGenAdminPage.jsx` | Created | DocGen Admin management tab |
| `petinsure360/bi-dashboard/src/App.jsx` | Modified | Added Agent Pipeline + DocGen Admin routes |

## Architecture

```
Customer Portal                    Backend                     DocGen Service
     |                                |                              |
     v                                v                              v
[Upload Docs] --> /api/docgen/upload --> ws7_docgen:8001/upload
     |                                |                              |
     |        (policy_id, pet_id,     |      (processes docs,        |
     |         customer_id)           |       creates claim)         |
     |                                |                              |
     v                                v                              v
[Notifications] <-- Socket.IO <-- docgen_completed <-- Background task
```

## How to Run (4 Terminals)

### Terminal 1: DocGen Service
```bash
cd "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc/src/ws7_docgen"
source ../../venv/bin/activate
export ANTHROPIC_API_KEY="your-api-key"
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Terminal 2: PetInsure360 Backend
```bash
cd "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360/backend"
source env_backend/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 3: Customer Portal
```bash
cd "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360/frontend"
npm run dev
```

### Terminal 4: BI Dashboard
```bash
cd "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360/bi-dashboard"
npm run dev -- --port 5174
```

## Service URLs

| Service | Port | URL |
|---------|------|-----|
| DocGen AI Service | 8001 | http://localhost:8001 |
| PetInsure360 Backend | 8000 | http://localhost:8000/docs |
| Customer Portal | 5173 | http://localhost:5173 |
| BI Dashboard | 5174 | http://localhost:5174 |

## What to Test Next Session

1. Start all 4 services in order (DocGen first)
2. Login to Customer Portal (http://localhost:5173)
3. Navigate to "Upload Documents" tab
4. Select a Policy and Pet, then upload vet documents
5. Check BI Dashboard (http://localhost:5174) for:
   - "Agent Pipeline" tab - see AI processing
   - "DocGen Admin" tab - manage document batches

## Key Features

- **Customer Portal**: Users select Policy + Pet before uploading docs (provides context to AI)
- **Real-time Notifications**: Socket.IO events for upload status
- **Legacy vs Agent Pipeline**: BI Dashboard shows both rule-based and AI pipelines
- **DocGen Admin**: Admin interface to manage document batches

## Notes

- DocGen service (ws7_docgen) is in the EIS POC project but used by PetInsure360
- Backend forwards uploads to DocGen service at port 8001
- All user context (customer_id, policy_id, pet_id) passed to agent
