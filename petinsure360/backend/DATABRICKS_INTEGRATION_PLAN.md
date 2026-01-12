# Databricks Integration Plan

## Objective
When user triggers each layer in the UI, invoke corresponding Databricks notebook and show real-time job status.

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────────┐
│   BI Dashboard  │────▶│  Backend API     │────▶│  Azure Databricks       │
│   (React)       │     │  (FastAPI)       │     │  Job: 591500457291311   │
└─────────────────┘     └──────────────────┘     └─────────────────────────┘
        │                       │                          │
        │ WebSocket             │ REST API                 │
        ▼                       ▼                          ▼
   Real-time UI          POST /jobs/run-now         ┌─────────────────┐
   Updates               GET /jobs/runs/get         │ 01_bronze       │
                                                    │ 02_silver       │
                                                    │ 03_gold         │
                                                    └─────────────────┘
```

---

## Implementation Steps

### Step 1: Create Databricks Service Module
**File:** `app/services/databricks.py`

```python
# Functions to implement:
- run_job(job_id) → Run entire ETL pipeline job
- run_notebook(notebook_path, parameters) → Run single notebook
- get_run_status(run_id) → Get job run status
- get_run_output(run_id) → Get notebook output
- cancel_run(run_id) → Cancel running job
```

**Databricks API Endpoints:**
| Action | API |
|--------|-----|
| Run Job | `POST /api/2.1/jobs/run-now` |
| Run Notebook | `POST /api/2.1/jobs/runs/submit` |
| Get Status | `GET /api/2.1/jobs/runs/get?run_id=X` |
| List Runs | `GET /api/2.1/jobs/runs/list?job_id=X` |

---

### Step 2: Modify Pipeline Endpoints
**File:** `app/api/pipeline.py`

#### Option A: Run Individual Notebooks (Recommended for Demo)
Each layer trigger invokes its specific notebook:

| Endpoint | Action |
|----------|--------|
| `POST /process/bronze-to-silver` | Invoke `01_bronze_ingestion` + `02_silver_transformations` |
| `POST /process/silver-to-gold` | Invoke `03_gold_aggregations` |

#### Option B: Run Full Job
Single trigger runs all 3 notebooks in sequence via the existing job.

**New Endpoint:**
```
POST /pipeline/databricks/trigger
{
  "layer": "bronze" | "silver" | "gold" | "all",
  "claim_ids": ["CLM-xxx", ...]
}
```

---

### Step 3: Add WebSocket Events for Real-Time Status

| Event | Payload | When |
|-------|---------|------|
| `databricks_job_started` | `{run_id, layer, job_url}` | Job submitted |
| `databricks_job_progress` | `{run_id, state, task}` | Task completes |
| `databricks_job_completed` | `{run_id, result, duration}` | Job finished |
| `databricks_job_failed` | `{run_id, error}` | Job failed |

---

### Step 4: UI Updates
**File:** `bi-dashboard/src/pages/PipelinePage.jsx`

1. **Job Status Indicator:**
   - Show "Running on Databricks..." with spinner when job active
   - Display job URL link to open in Databricks UI

2. **Progress Tracking:**
   - Show which notebook is currently executing
   - Display estimated time remaining

3. **Completion Status:**
   - Show success/failure with duration
   - Display records processed count

---

## Databricks Credentials

| Variable | Value |
|----------|-------|
| `DATABRICKS_HOST` | `https://adb-7405619408519767.7.azuredatabricks.net` |
| `DATABRICKS_TOKEN` | `<configured in environment>` |
| `DATABRICKS_JOB_ID` | `591500457291311` |

> **Note:** Token is configured as environment variable in AWS App Runner, not stored in code.

---

## API Examples

### Run Entire Job
```bash
curl -X POST "${DATABRICKS_HOST}/api/2.1/jobs/run-now" \
  -H "Authorization: Bearer ${DATABRICKS_TOKEN}" \
  -d '{"job_id": 591500457291311}'
```

### Run Single Notebook
```bash
curl -X POST "${DATABRICKS_HOST}/api/2.1/jobs/runs/submit" \
  -H "Authorization: Bearer ${DATABRICKS_TOKEN}" \
  -d '{
    "run_name": "Bronze Layer - Manual Trigger",
    "existing_cluster_id": "1223-104240-2rys4e5v",
    "notebook_task": {
      "notebook_path": "/PetInsure360/01_bronze_ingestion"
    }
  }'
```

### Check Run Status
```bash
curl -X GET "${DATABRICKS_HOST}/api/2.1/jobs/runs/get?run_id=12345" \
  -H "Authorization: Bearer ${DATABRICKS_TOKEN}"
```

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `app/services/databricks.py` | **CREATE** - Databricks API client |
| `app/api/pipeline.py` | **MODIFY** - Add Databricks invocation |
| `bi-dashboard/src/pages/PipelinePage.jsx` | **MODIFY** - Add job status UI |

---

## Demo Flow

1. User clicks "Process Bronze → Silver" in UI
2. Backend calls Databricks API to run notebook
3. WebSocket emits `databricks_job_started` with job URL
4. UI shows "Running on Databricks..." with link
5. Backend polls job status every 5 seconds
6. WebSocket emits `databricks_job_progress` updates
7. Job completes → WebSocket emits `databricks_job_completed`
8. UI shows success with duration and records processed

---

## Estimated Implementation

| Component | Complexity |
|-----------|------------|
| Databricks service module | Medium |
| Pipeline endpoint changes | Low |
| WebSocket events | Low |
| UI updates | Medium |

---

## Risk Mitigation

1. **Cluster startup time:** Job clusters take ~2-3 min to start
   - Solution: Use "all-purpose" cluster or show startup progress

2. **Cost:** Running clusters costs money
   - Solution: Auto-terminate after 10 min idle

3. **Error handling:** Jobs can fail
   - Solution: Proper error messages and retry UI
