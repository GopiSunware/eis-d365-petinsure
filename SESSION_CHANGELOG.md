# Session Changelog

Recent development sessions and changes made to the PetInsure360 / EIS Dynamics platform.

---

## Session: January 11, 2026

### Summary
Fixed duplicate claims bug, added pipeline execution proof, and improved UI feedback for document processing.

### Issues Fixed

#### 1. Duplicate Claims in Recent Claims List (Issue #13)
**Problem:** Same claim appeared twice in the "Recent Claims" table.

**Root Cause:** `add_claim()` in `insights.py` was called twice:
1. When claim submitted to Bronze layer (line 392 in `pipeline.py`)
2. When claim processed to Gold layer (line 647 in `pipeline.py`)

**Fix:** Added duplicate check in `petinsure360/backend/app/services/insights.py`:
```python
def add_claim(self, claim_data):
    claim_id = str(claim_data.get('claim_id', ''))
    if claim_id and len(self._claims) > 0:
        existing = self._claims[self._claims['claim_id'].astype(str) == claim_id]
        if not existing.empty:
            print(f"Claim {claim_id} already exists - skipping duplicate add")
            return  # Skip duplicate
```

**Files Changed:**
- `petinsure360/backend/app/services/insights.py`

---

#### 2. Pipeline Execution Proof (Issue #12)
**Problem:** When user clicks "Process Bronze → Silver" or "Process Silver → Gold", there was no way to know what processing actually occurred. User asked: "how do we know medallion notebook executed?"

**Finding:** The medallion architecture processing is done **entirely in Python** (in-memory), NOT via Databricks notebooks.

**Fix:** Added comprehensive execution info and processing proof to API responses.

**Backend Changes (`petinsure360/backend/app/api/pipeline.py`):**

1. **Pipeline Status** now includes `execution_info`:
```json
{
  "execution_info": {
    "mode": "python_local",
    "engine": "PetInsure360 Backend (Python/FastAPI)",
    "databricks_connected": false,
    "description": "Medallion architecture processing is simulated in Python...",
    "note": "To enable actual Databricks notebook execution, configure DATABRICKS_HOST and DATABRICKS_TOKEN..."
  }
}
```

2. **Bronze → Silver Response** now includes:
```json
{
  "execution_mode": "python_local",
  "execution_engine": "PetInsure360 Backend (Python/FastAPI)",
  "notebook_executed": false,
  "transformations_applied": ["Data type standardization", "Line items validation", ...],
  "processing_proof": [
    {
      "claim_id": "CLM-xxx",
      "completeness_score": 100,
      "validity_score": 85,
      "overall_quality_score": 91,
      "processed_at": "2026-01-11T..."
    }
  ]
}
```

3. **Silver → Gold Response** now includes:
```json
{
  "processing_proof": [
    {
      "claim_id": "CLM-xxx",
      "claim_amount": 5000,
      "estimated_reimbursement": 3800,
      "customer_name": "Demo User",
      "customer_tier": "Gold",
      "processing_priority": "Normal",
      "processed_at": "2026-01-11T..."
    }
  ]
}
```

**Frontend Changes (`petinsure360/bi-dashboard/src/pages/PipelinePage.jsx`):**

1. **Execution Mode Banner** - Shows at top of Pipeline page:
   - Amber banner for "Python Local Processing"
   - Green banner for "Databricks Connected" (if configured)

2. **Processing Proof Panel** - Appears after clicking process buttons:
   - Shows execution engine
   - Lists all transformations applied
   - Table of claims with calculated values (scores, reimbursements)

**Files Changed:**
- `petinsure360/backend/app/api/pipeline.py`
- `petinsure360/bi-dashboard/src/pages/PipelinePage.jsx`

---

### Documentation Updated

1. **DEPLOYMENT_CHECKLIST.md** - Added:
   - Issue 12: Rule Engine Pipeline Execution Mode
   - Issue 13: Duplicate Claims in Recent Claims List
   - Verification commands for both issues

2. **TROUBLESHOOTING.md** - Added:
   - "Duplicate Claims in Recent Claims List" quick check
   - "Pipeline Execution Mode Not Clear" quick check

---

### Deployed Services

| Service | Action | Status |
|---------|--------|--------|
| PetInsure360 Backend | Rebuilt & deployed to ECR/App Runner | ✅ RUNNING |
| BI Dashboard | Rebuilt & deployed to S3 | ✅ 200 OK |

**Verification Commands:**
```bash
# Check execution info
curl -s "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/pipeline/status" | jq '.execution_info'

# Check duplicate fix - each claim_id should appear only once
curl -s "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/insights/claims?limit=5" | jq '.claims[].claim_id'
```

---

## Session: January 10, 2026 (Earlier)

### Summary
Fixed multiple document upload and display issues, improved customer-facing error handling.

### Issues Fixed

#### 1. BI Dashboard Doc Processing Shows Wrong Data
**Problem:** DocGenAdminPage.jsx was calling wrong URL (`VITE_DOCGEN_URL` instead of `VITE_API_URL`).

**Fix:**
- Changed `DocGenAdminPage.jsx` to use `VITE_API_URL`
- Added `/api/docgen/batches` endpoint to backend

**Files Changed:**
- `petinsure360/bi-dashboard/src/pages/DocGenAdminPage.jsx`
- `petinsure360/backend/app/api/docgen.py`

---

#### 2. Customer Portal Showing Scary Error Messages
**Problem:** Customer Portal showed "Failed" status with technical error messages.

**User Quote:** "client side we should never show any error"

**Fix:**
- Changed status from "Failed" (red) to "In Review" (amber)
- Changed error message to friendly text: "Your claim is being reviewed by our team..."

**Files Changed:**
- `petinsure360/frontend/src/pages/UploadDocsPage.jsx`

---

#### 3. Demo Customers Not at Top of Customer 360
**Problem:** DEMO-001, DEMO-002 weren't appearing at top of customer list.

**Root Cause:** Frontend sorts by `customer_since` date, but demo customers had old dates (2024-01-01).

**Fix:** Updated dates to 2026-01-10 and 2026-01-09 in `insights.py`.

**Files Changed:**
- `petinsure360/backend/app/api/insights.py` (DEMO_CUSTOMERS_360)

---

#### 4. Admin Can't See Error Details in BI Dashboard
**Problem:** Admins couldn't see why document processing failed.

**Fix:** Added error message display in:
- Table row (truncated)
- Modal detail view (full message)

**Files Changed:**
- `petinsure360/bi-dashboard/src/pages/DocGenAdminPage.jsx`

---

## AWS Service URLs (Current)

| Service | URL |
|---------|-----|
| PetInsure360 Backend | https://fucf3fwwwv.us-east-1.awsapprunner.com |
| Claims Data API | https://9wvcjmrknc.us-east-1.awsapprunner.com |
| Agent Pipeline | https://qi2p3x5gsm.us-east-1.awsapprunner.com |
| DocGen Service | https://tbkh2svcwm.us-east-1.awsapprunner.com |
| Customer Portal | http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com |
| BI Dashboard | http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com |
| Agent Portal | http://eis-agent-portal.s3-website-us-east-1.amazonaws.com |
| Admin Portal | http://eis-admin-portal.s3-website-us-east-1.amazonaws.com |

---

## Known Limitations

1. **Pipeline Processing** - Bronze → Silver → Gold is simulated in Python. To enable actual Databricks notebooks:
   - Set `DATABRICKS_HOST` environment variable
   - Set `DATABRICKS_TOKEN` environment variable
   - Implement Databricks Jobs API calls in `pipeline.py`

2. **Demo Data** - In-memory storage resets on backend restart. Demo data is re-seeded via `/api/customers/seed-demo` endpoint.

3. **WebSocket** - Real-time updates require AWS API Gateway WebSocket (wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod)
