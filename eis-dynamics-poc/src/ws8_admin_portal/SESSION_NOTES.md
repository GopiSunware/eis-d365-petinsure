# Session Notes - EIS Admin Portal

**Date:** January 4, 2026
**Project:** ws8_admin_portal
**Location:** `/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc/src/ws8_admin_portal/`

---

## Session Summary

### Session 2 (Current)
This session focused on:
1. **Real Audit Logging** - Added audit middleware and frontend event tracking
2. **User Synchronization** - Shared users between Admin Portal and Agent Portal (PetInsure)
3. **Agent Portal Authentication** - Added login/logout using Admin Portal's user system

### Session 1
Made Cost Monitor display **real data only** (no mock/fake data) and updated documentation.

---

## Session 2 - Completed Tasks

### 1. Real Audit Logging

**Backend:**
- Added `AuditLoggerMiddleware` to `backend/app/main.py` to log all HTTP requests
- Added `/api/v1/audit/event` endpoint in `backend/app/routers/audit.py` for frontend event logging
- Backend already had audit service logging for CRUD operations in routers

**Frontend:**
- Created `frontend/lib/useAuditLog.ts` - Custom hook for audit logging
- Created `frontend/components/AuditTracker.tsx` - Automatic page view tracking
- Added AuditTracker to `frontend/app/layout.tsx` to track all page visits
- Added `auditApi.logEvent()` to `frontend/lib/api.ts` for frontend event logging

**What Gets Logged:**
- Page views (automatic on navigation)
- User CRUD operations (create, update, delete)
- Config changes (via approval workflow)
- Login/logout events
- Button clicks and form submissions (via manual hook calls)

### 2. Shared User Authentication (Admin Portal ↔ Agent Portal)

**Agent Portal (ws4_agent_portal) - New Files:**
- `lib/auth.ts` - Auth API client connecting to Admin Portal backend
- `lib/AuthContext.tsx` - React context for authentication state
- `components/AuthenticatedLayout.tsx` - Conditional layout for login vs authenticated pages
- `app/login/page.tsx` - Login page with demo credentials
- `app/login/layout.tsx` - Minimal layout for login page

**Agent Portal - Updated Files:**
- `app/providers.tsx` - Added AuthProvider
- `app/layout.tsx` - Uses AuthenticatedLayout for conditional sidebar/header
- `components/Header.tsx` - Shows user info and logout button
- `.env.local` - Updated ADMIN_API_URL to port 3001
- `.env.example` - Updated with correct port

**How It Works:**
1. Agent Portal calls Admin Portal's `/api/v1/auth/login` endpoint
2. On success, stores JWT token in localStorage (`agent_token`)
3. Protected routes redirect to `/login` if not authenticated
4. Logout clears token and redirects to login
5. Same user credentials work on both portals

**Default Credentials:**
- Email: `admin@eis-dynamics.com`
- Password: `admin123!`

### 3. Configuration Updates

**Port Configuration:**
- Admin Portal Backend: `http://localhost:3001`
- Admin Portal Frontend: `http://localhost:3000`
- Agent Portal uses Admin Portal Backend for auth

**Environment Files Updated:**
- `ws4_agent_portal/.env.local` - `NEXT_PUBLIC_ADMIN_API_URL=http://localhost:3001`
- `ws4_agent_portal/.env.example` - Updated with correct port

---

## Session 1 - Completed Tasks

### 1. Removed All Mock Data

**Budget Alerts:**
- Removed hardcoded mock budgets (`$857/$1,500` and `$412/$500`) from `backend/app/routers/costs.py`
- Budget alerts now return empty list until user creates real budgets
- Dashboard shows "No active budget alerts" when none configured

**AI Usage:**
- Removed mock AI token data from `backend/app/services/ai_usage_service.py`
- Replaced `_get_mock_azure_openai_usage()` and `_get_mock_aws_bedrock_usage()` with `_get_empty_usage()` that returns zeros
- Removed fake Document Intelligence and Database usage from platform summary
- AI Usage tab shows helpful message: "No AI/LLM API usage detected" when no data

**Frontend Updates:**
- Updated `frontend/app/costs/page.tsx` to hide empty sections
- Platform Cost Breakdown only shows when data exists
- Usage by Model table hidden when empty
- Document Intelligence and Database cards only shown when data exists

### 2. Real Data Sources Configured

**Azure Cost Management:**
- Uses `DefaultAzureCredential` (works with `az login` locally)
- Subscription ID: `7c6fe42e-75ab-4c1c-beea-4eaee73170d9`
- Resource group filter: `eis,dynamics,sunware`
- Real data showing: $4.24 (NAT Gateway, Databricks, Virtual Network, etc.)

**AWS Cost Explorer:**
- Credentials configured from `~/.aws/credentials`
- Service filter: `Bedrock,Lambda,S3,API Gateway,CloudWatch`
- Currently showing $0.00 (no AWS usage in filtered services)

### 3. AI Token Usage Tracking (Added)

**Backend:**
- Created `backend/app/models/ai_usage.py` - Token pricing, usage models
- Created `backend/app/services/ai_usage_service.py` - Fetches from Azure Monitor & CloudWatch
- Added endpoints: `/api/v1/costs/ai-usage` and `/api/v1/costs/platform-usage`

**Frontend:**
- Added "AI Usage" tab to Cost Monitor page
- Shows: Total tokens, cost, requests, avg cost/request
- Breakdown by provider (Azure OpenAI, AWS Bedrock)
- Breakdown by model (GPT-4o, Claude, etc.)

### 4. Documentation Updated

- Created `README.md` - Full project documentation
- Updated `.env.example` - All configuration options
- Updated `docker-compose.yml` - Added filter environment variables

---

## Current State

### Working Features
- Dashboard with real Azure costs
- Cost Monitor (Overview, Azure, AWS tabs)
- AI Usage tab (shows zeros - no AI services deployed)
- Budget Alerts tab (empty - user can create)
- Audit Logs
- Approvals (maker-checker workflow)
- User Management
- Configuration pages (AI Config, Claims Rules, Policy Config, Rating)

### Port Configuration
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:3001`

### Data Status
| Feature | Status | Notes |
|---------|--------|-------|
| Azure Costs | Real | $4.24 MTD from Cost Management API |
| AWS Costs | Real | $0.00 (no usage in filtered services) |
| AI Token Usage | Real | $0.00 (no Azure OpenAI/Bedrock deployed) |
| Budget Alerts | Empty | User-created only, no mock data |
| Document Intelligence | Not tracked | Will show when integrated |
| Database (Cosmos DB) | Not tracked | Will show when integrated |

---

## Known Issues / TODO

### TypeScript Errors (Pre-existing)
The following pages have TypeScript errors due to model mismatches:
- `app/claims-rules/page.tsx` - Field names don't match backend types
- `app/policy-config/page.tsx` - Field names don't match backend types

These errors exist but don't affect runtime (Next.js still compiles).

### Future Enhancements
1. Add Document Intelligence usage tracking (when service is used)
2. Add Cosmos DB usage tracking (when database is connected)
3. Fix TypeScript types for claims-rules and policy-config pages
4. Add budget alert creation UI functionality
5. Add manual audit logging hooks to config edit forms
6. Add role-based access control to Agent Portal based on user permissions

---

## File Locations

### Documentation
- Main README: `ws8_admin_portal/README.md`
- Session Notes: `ws8_admin_portal/SESSION_NOTES.md`
- Environment Example: `ws8_admin_portal/.env.example`

### Key Backend Files (Admin Portal)
- Main: `backend/app/main.py` - FastAPI app with middleware
- Config: `backend/app/config.py`
- Audit Router: `backend/app/routers/audit.py` - Includes frontend event endpoint
- Audit Service: `backend/app/services/audit_service.py`
- Audit Middleware: `backend/app/middleware/audit_logger.py`
- Cost Router: `backend/app/routers/costs.py`
- AI Usage Service: `backend/app/services/ai_usage_service.py`
- Azure Cost Service: `backend/app/services/azure_cost_service.py`
- AWS Cost Service: `backend/app/services/aws_cost_service.py`

### Key Frontend Files (Admin Portal)
- Layout: `frontend/app/layout.tsx` - Includes AuditTracker
- Costs Page: `frontend/app/costs/page.tsx`
- Dashboard: `frontend/app/page.tsx`
- API Client: `frontend/lib/api.ts` - Includes audit event logging
- Audit Hook: `frontend/lib/useAuditLog.ts`
- Audit Tracker: `frontend/components/AuditTracker.tsx`

### Agent Portal Files (ws4_agent_portal)
- Auth API: `lib/auth.ts`
- Auth Context: `lib/AuthContext.tsx`
- Auth Layout: `components/AuthenticatedLayout.tsx`
- Login Page: `app/login/page.tsx`
- Header: `components/Header.tsx` - Shows user info

### Configuration Files
- Admin Backend env: `ws8_admin_portal/backend/.env`
- Admin Frontend env: `ws8_admin_portal/frontend/.env.local`
- Agent Portal env: `ws4_agent_portal/.env.local`
- Docker: `ws8_admin_portal/docker-compose.yml`

---

## How to Start

```bash
# Backend
cd backend
source venv/bin/activate  # if using venv
uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload

# Frontend (separate terminal)
cd frontend
npm run dev
```

Access at: http://localhost:3000

---

## Credentials Location

- Azure: Uses `az login` (DefaultAzureCredential)
- AWS: Configured in `backend/.env` (copied from `~/.aws/credentials`)

**Note:** Do not commit `.env` files with real credentials!
