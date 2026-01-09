# Troubleshooting Guide

Common issues and solutions for the PetInsure360 and EIS Dynamics projects.

---

## CRITICAL: Complete Service List

**There are 12 total services that must be running for full functionality.**

### PetInsure360 (3 services)
| Port | Service | Entry Point | Notes |
|------|---------|-------------|-------|
| 3000 | Customer Portal | `npm run dev` | React/Vite UI |
| 3001 | BI Dashboard | `npm run dev` | React/Vite UI |
| 3002 | Backend API | `uvicorn app.main:socket_app` | **MUST use socket_app, NOT app** |

### EIS Dynamics Backend (7 services)
| Port | Service | Entry Point | Notes |
|------|---------|-------------|-------|
| 8000 | Claims Data API | `uvicorn app.main:app` | **Has Chat API endpoints** |
| 8002 | WS2 AI Claims | `uvicorn app.main:app` | Often forgotten! |
| 8003 | WS3 Integration | `uvicorn app.main:app` | EIS Mock proxy |
| 8005 | WS5 Rating Engine | `uvicorn app.main:app` | Often forgotten! |
| 8006 | WS6 Agent Pipeline | `uvicorn app.main:app` | LangGraph agents |
| 8007 | WS7 DocGen | `uvicorn app.main:app` | Often forgotten! |
| 8008 | WS8 Admin Backend | `uvicorn app.main:app` | Admin API |

### EIS Dynamics Frontend (2 services)
| Port | Service | Entry Point | Notes |
|------|---------|-------------|-------|
| 8080 | WS4 Agent Portal | `npm run dev` | Next.js UI |
| 8081 | WS8 Admin Portal | `npm run dev` | Next.js UI |

### Quick Status Check Script
```bash
for port in 3000 3001 3002 8000 8002 8003 8005 8006 8007 8008 8080 8081; do
  STATUS=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 2 http://localhost:$port/health 2>/dev/null)
  [ "$STATUS" = "000" ] && STATUS=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 2 http://localhost:$port/ 2>/dev/null)
  [ "$STATUS" = "200" ] && ICON="✅" || ICON="❌"
  echo "Port $port: $ICON ($STATUS)"
done
```

---

## PetInsure360 Issues

### 1. WebSocket Connection Failed

**Error:**
```
WebSocket connection to 'ws://localhost:3002/socket.io/?EIO=4&transport=websocket' failed
```

**Cause:** Backend started with `app` instead of `socket_app`. The Socket.IO wrapper is not active.

**Solution:** ALWAYS use `socket_app` entry point:
```bash
cd petinsure360/backend
source venv/bin/activate
uvicorn app.main:socket_app --host 0.0.0.0 --port 3002 --reload
#                ^^^^^^^^^^^ CRITICAL: Must be socket_app, NOT app
```

**Verify fix:**
```bash
# Health check - should show "websocket":"enabled"
curl http://localhost:3002/health

# Socket.IO check - should return JSON with "sid" and "upgrades":["websocket"]
curl 'http://localhost:3002/socket.io/?EIO=4&transport=polling'
```

**Root cause in code:** `app/main.py` line ~94:
```python
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
```

---

### 2. 307 Redirect on API Endpoints

**Error:** `GET /api/pets` returns 307 redirect to `/api/pets/`

**Cause:** FastAPI's default `redirect_slashes=True` behavior.

**Solution:** Fixed in `app/main.py`:
```python
app = FastAPI(..., redirect_slashes=False)
```

Plus dual route decorators in endpoint files:
```python
@router.get("/")
@router.get("")  # Handle both with and without trailing slash
async def list_items(...):
```

---

### 3. Schema Validation Errors (422)

**Error:** `422 Unprocessable Entity` on customer/claim creation

**Cause:** Frontend sends different field names than backend expects.

**Solution:** Use flexible schemas with aliases and helper methods in `app/models/schemas.py`:
- `CustomerCreate`: `address` alias for `address_line1`, optional `date_of_birth`
- `ClaimCreate`: `amount` alias for `claim_amount`, default `claim_category`, helper methods

---

## EIS Dynamics Issues

### 1. CORS Errors

**Error:**
```
Access to XMLHttpRequest at 'http://localhost:8003/api/v1/eis/policies' from origin 'http://localhost:8080'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
```

**Cause:** EIS backend services have empty `cors_origins` by default from `eis_common.config`.

**Solution:** Fixed in code - services now default to `["*"]` when `CORS_ORIGINS` env var is not set:
```python
# In each service's main.py
cors_origins = settings.cors_origins if settings.cors_origins else ["*"]
```

**Services that needed this fix:**
- `ws2_ai_claims/app/main.py`
- `ws3_integration/app/main.py`
- `ws5_rating_engine/app/main.py`

**Verify CORS:**
```bash
curl -I -X OPTIONS http://localhost:8003/api/v1/eis/policies \
  -H "Origin: http://localhost:8080" \
  -H "Access-Control-Request-Method: GET"
# Should show: access-control-allow-origin: http://localhost:8080
```

---

### 2. Chat API Provider Errors

**Error:**
```
GET http://localhost:8003/api/chat/providers 404 (Not Found)
GET http://localhost:8008/api/chat/providers 404 (Not Found)
Failed to fetch AI providers
```

**Cause:** Chat API endpoints are on port **8000** (Claims Data API), NOT on 8003 or 8008. Frontend was configured to call wrong ports.

**Solution:** Fixed in `ws4_agent_portal/lib/chatApi.ts`:
```typescript
// Chat API is on Claims Data API (port 8000) - separate from CLAIMS_API_URL (port 8003)
const API_BASE = process.env.NEXT_PUBLIC_CHAT_API_URL || 'http://localhost:8000';
```

**Verify Chat API:**
```bash
curl http://localhost:8000/api/chat/providers
# Should return: {"providers":{"openai":{...},"anthropic":{...}},"enabled":[...],"default":"openai"}
```

**Key insight:** The Chat API lives on **Claims Data API (8000)**, not on Integration (8003) or Admin (8008).

---

### 3. Missing Services

**Symptom:** Various 404 errors or connection refused errors.

**Cause:** Not all 7 EIS backend services were started. Commonly missed:
- **8002** - WS2 AI Claims
- **8005** - WS5 Rating Engine
- **8007** - WS7 DocGen

**Solution:** Start ALL backend services. Use this script:
```bash
EIS_ROOT="/path/to/eis-dynamics-poc"

# Start all EIS backend services
for ws in "shared/claims_data_api:8000" "ws2_ai_claims:8002" "ws3_integration:8003" \
          "ws5_rating_engine:8005" "ws6_agent_pipeline:8006" "ws7_docgen:8007"; do
  DIR=$(echo $ws | cut -d: -f1)
  PORT=$(echo $ws | cut -d: -f2)
  cd "$EIS_ROOT" && source venv/bin/activate && \
    cd "src/$DIR" && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT &
done

# Start WS8 Admin Backend (different path)
cd "$EIS_ROOT/src/ws8_admin_portal/backend" && \
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8008 &
```

---

## API Endpoint Reference

### Chat API (Port 8000 - Claims Data API)
```
GET  /api/chat/providers  - List available AI providers
GET  /api/chat/status     - Check chat availability
POST /api/chat            - Send chat message
```

### EIS Mock API (Port 8003 - WS3 Integration)
```
GET  /api/v1/eis/claims   - List claims
GET  /api/v1/eis/policies - List policies
GET  /api/v1/eis/customers - List customers
```

### Agent Pipeline (Port 8006)
```
POST /api/v1/pipeline/trigger - Trigger claim processing
GET  /api/v1/pipeline/status  - Get pipeline status
```

### DocGen (Port 8007)
```
POST /api/v1/docgen/batch/from-claim - Create batch from claim
POST /api/v1/docgen/upload           - Upload documents
```

---

## Environment Variables

### PetInsure360 Backend
```bash
# In petinsure360/backend/.env
DOCGEN_SERVICE_URL=http://localhost:8007
AGENT_PIPELINE_URL=http://localhost:8006
```

### EIS Dynamics
```bash
# In eis-dynamics-poc/src/.env
CORS_ORIGINS=  # Leave empty for ["*"] in dev
```

### Frontend Portals
```bash
# ws4_agent_portal/.env.local
NEXT_PUBLIC_CLAIMS_API_URL=http://localhost:8003
NEXT_PUBLIC_CHAT_API_URL=http://localhost:8000    # Chat is on 8000!
NEXT_PUBLIC_PIPELINE_API_URL=http://localhost:8006
NEXT_PUBLIC_DOCGEN_API_URL=http://localhost:8007

# ws8_admin_portal/frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8008
NEXT_PUBLIC_CHAT_API_URL=http://localhost:8000    # Chat is on 8000!
```

---

## Common Mistakes to Avoid

1. **Starting PetInsure360 backend with `app` instead of `socket_app`**
   - WebSocket/Socket.IO will not work
   - Always use: `uvicorn app.main:socket_app`

2. **Forgetting to start WS2, WS5, or WS7 services**
   - These are often missed but required for full functionality
   - Check all 7 EIS backend ports: 8000, 8002, 8003, 8005, 8006, 8007, 8008

3. **Calling Chat API on wrong port**
   - Chat API is on **8000** (Claims Data API)
   - NOT on 8003 (Integration) or 8008 (Admin)

4. **CORS not configured for development**
   - EIS services default to empty cors_origins
   - Code fix: `cors_origins = settings.cors_origins if settings.cors_origins else ["*"]`

5. **API endpoints with/without trailing slash**
   - Use dual decorators: `@router.get("/")` and `@router.get("")`
   - Set `redirect_slashes=False` in FastAPI app

---

## Startup Checklist

Before testing, verify:

- [ ] All 12 services are running (use status check script above)
- [ ] PetInsure360 backend uses `socket_app` entry point
- [ ] Chat API responds on port 8000: `curl http://localhost:8000/api/chat/providers`
- [ ] CORS headers present: `curl -I http://localhost:8003/api/v1/eis/claims`
- [ ] Socket.IO working: `curl http://localhost:3002/socket.io/?EIO=4&transport=polling`
