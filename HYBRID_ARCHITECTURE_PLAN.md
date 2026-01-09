# Hybrid Architecture Implementation Plan

**Date:** 2026-01-09
**Status:** PLANNING
**Goal:** Connect AWS compute layer to Azure data platform (medallion architecture)

---

## Overview

Connect AWS-hosted APIs to Azure ADLS Gen2 Gold layer to provide real production data while maintaining demo data for offline/fallback scenarios.

```
┌─────────────────────────────────────────────────────────────────┐
│                     AWS (Compute Layer)                          │
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │ Claims Data API  │    │  Agent Pipeline  │                   │
│  │ (App Runner)     │    │  (App Runner)    │                   │
│  └────────┬─────────┘    └────────┬─────────┘                   │
│           │                       │                              │
│           ▼                       ▼                              │
│  ┌─────────────────────────────────────────┐                    │
│  │         Azure Data Service              │                    │
│  │  (New module - reads from Azure)        │                    │
│  └────────────────┬────────────────────────┘                    │
└───────────────────┼──────────────────────────────────────────────┘
                    │
                    ▼ (HTTPS + SAS Token)
┌───────────────────────────────────────────────────────────────────┐
│                     Azure (Data Platform)                         │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │   Bronze    │→ │   Silver    │→ │    Gold     │               │
│  │ (Raw JSON)  │  │ (Cleaned)   │  │ (Analytics) │               │
│  └─────────────┘  └─────────────┘  └──────┬──────┘               │
│                                           │                       │
│  Storage Account: petinsud7i43            │                       │
│  Databricks: petinsure360-databricks-dev  │                       │
│  Key Vault: petins-kv-ud7i43              │                       │
└───────────────────────────────────────────┘
```

---

## Implementation Steps

### Phase 1: Azure Data Access Layer (Backend)

**1.1 Create Azure Service Module**

Location: `eis-dynamics-poc/src/shared/claims_data_api/app/services/azure_data_service.py`

```python
# Key functionality:
- Connect to Azure ADLS Gen2 using SAS token or Service Principal
- Read Parquet files from Gold layer
- Convert to Pandas/JSON for API responses
- Implement caching to reduce Azure calls
```

**Gold Layer Tables to Access:**
| Table | Path | Description |
|-------|------|-------------|
| customer_360_view | gold/customer_360_view/ | Unified customer data |
| claims_analytics | gold/claims_analytics/ | Claims metrics |
| monthly_kpis | gold/monthly_kpis/ | Executive KPIs |
| risk_scoring | gold/risk_scoring/ | Risk assessments |
| provider_performance | gold/provider_performance/ | Vet analytics |

**1.2 Update Environment Variables**

Add to Claims Data API:
```env
# Azure Data Source Configuration
USE_AZURE_DATA=false  # Toggle demo vs real data
AZURE_STORAGE_ACCOUNT=petinsud7i43
AZURE_STORAGE_SAS_TOKEN=<SAS token with read permissions>
AZURE_GOLD_CONTAINER=gold
DATA_CACHE_TTL=300  # Cache for 5 minutes
```

**1.3 Create Data Source Toggle Endpoint**

```
GET /api/v1/data-source/status
PUT /api/v1/data-source/toggle
```

### Phase 2: Frontend UI Toggle

**2.1 Add Data Source Selector**

Location: BI Dashboard Settings page

```jsx
// Component: DataSourceToggle
// Options: "Demo Data (Local)" | "Azure Gold Layer (Live)"
// Shows connection status, last sync time, data freshness
```

**2.2 Update Insights Endpoints**

Modify existing endpoints to check data source:
- `/api/insights/summary`
- `/api/insights/customers`
- `/api/insights/claims`
- `/api/insights/kpis`

### Phase 3: Fallback & Caching

**3.1 Implement Smart Fallback**

```python
def get_customers():
    if USE_AZURE_DATA:
        try:
            data = azure_service.read_gold_table("customer_360_view")
            cache.set("customers", data, ttl=300)
            return data
        except AzureConnectionError:
            logger.warning("Azure unavailable, using demo data")
            return demo_data.get_customers()
    return demo_data.get_customers()
```

**3.2 Implement Caching Layer**

- Use in-memory cache (Redis optional for production)
- TTL: 5 minutes for frequently accessed data
- Manual refresh endpoint for forced sync

---

## Potential Issues & Mitigations

### 1. Authentication (CRITICAL)

**Issue:** AWS services need secure access to Azure ADLS

**Mitigations:**
- **Option A (Recommended):** Use SAS Token with limited permissions
  - Read-only access to Gold container
  - Time-limited (rotate monthly)
  - Store in AWS Secrets Manager

- **Option B:** Azure Service Principal
  - Create service principal with RBAC
  - Assign "Storage Blob Data Reader" role
  - Store client_id, client_secret in AWS Secrets Manager

**Implementation:**
```python
# Using SAS Token (simpler)
from azure.storage.filedatalake import DataLakeServiceClient

sas_token = os.getenv("AZURE_STORAGE_SAS_TOKEN")
account_url = f"https://{account_name}.dfs.core.windows.net"
service_client = DataLakeServiceClient(account_url, credential=sas_token)
```

### 2. Network Latency

**Issue:** Cross-cloud calls add 50-200ms latency

**Mitigations:**
- Cache frequently accessed data (5-minute TTL)
- Batch multiple reads into single requests
- Async data fetching for non-critical paths
- Pre-warm cache on service startup

### 3. Data Format Compatibility

**Issue:** Databricks Delta Lake format may not be directly readable

**Mitigations:**
- **Option A:** Export Gold tables to Parquet files (no Delta metadata)
- **Option B:** Use Databricks SQL endpoint (additional cost ~$50/month)
- **Option C:** Run daily export job to create Parquet snapshots

**Recommended:** Option A - Parquet export
```python
# In Databricks notebook (add to gold_aggregations.py):
df_customer_360.write.mode("overwrite").parquet(f"{gold_path}/exports/customer_360")
```

### 4. Azure Data Egress Costs

**Issue:** Azure charges for data leaving Azure (~$0.087/GB)

**Mitigations:**
- Cache aggressively (reduces repeated reads)
- Compress data transfers
- Read only changed data (delta sync)
- Estimated cost: ~$5-10/month for typical usage

### 5. Schema Evolution

**Issue:** Gold layer schema may change after Databricks updates

**Mitigations:**
- Version API endpoints (/v1/, /v2/)
- Graceful degradation (return partial data if columns missing)
- Schema validation with defaults
- Monitor for schema changes

### 6. Availability & Reliability

**Issue:** Azure ADLS or network may be temporarily unavailable

**Mitigations:**
- Always maintain demo data as fallback
- Circuit breaker pattern (after 3 failures, use demo for 5 minutes)
- Health check endpoint for Azure connectivity
- Alert on connectivity failures

---

## Files to Create/Modify

### New Files

| File | Purpose |
|------|---------|
| `claims_data_api/app/services/azure_data_service.py` | Azure ADLS connection |
| `claims_data_api/app/services/data_source_service.py` | Toggle logic |
| `bi-dashboard/src/pages/SettingsPage.jsx` | UI toggle (if not exists) |

### Modified Files

| File | Changes |
|------|---------|
| `claims_data_api/app/services/insights_service.py` | Add Azure data path |
| `claims_data_api/requirements.txt` | Add azure-storage-file-datalake |
| `bi-dashboard/.env.production` | Add data source config |

---

## Azure Setup Required

### 1. Create SAS Token

```bash
az login
az storage container generate-sas \
    --account-name petinsud7i43 \
    --name gold \
    --permissions r \
    --expiry 2026-12-31 \
    --output tsv
```

### 2. Export Gold Tables to Parquet

Add to Databricks notebook (03_gold_aggregations.py):
```python
# Export for external access
export_path = f"{gold_path}/exports"

df_customer_360.write.mode("overwrite").parquet(f"{export_path}/customer_360")
df_claims_analytics.write.mode("overwrite").parquet(f"{export_path}/claims_analytics")
df_monthly_kpis.write.mode("overwrite").parquet(f"{export_path}/monthly_kpis")
```

### 3. Store SAS Token in AWS

```bash
aws secretsmanager create-secret \
    --name petinsure360/azure-sas-token \
    --secret-string '{"sas_token":"YOUR_SAS_TOKEN"}' \
    --profile sunwaretech
```

---

## Testing Plan

### 1. Unit Tests
- Mock Azure responses
- Test fallback to demo data
- Test cache behavior

### 2. Integration Tests
- Verify Azure connection
- Test data format compatibility
- Measure latency

### 3. End-to-End Tests
- Toggle data source in UI
- Verify data changes in dashboards
- Test Azure offline scenario

---

## Timeline

| Phase | Tasks | Status |
|-------|-------|--------|
| Phase 1 | Azure Data Service | Pending |
| Phase 2 | UI Toggle | Pending |
| Phase 3 | Fallback & Caching | Pending |
| Testing | All test types | Pending |

---

## Dependencies

```
# Add to requirements.txt
azure-storage-file-datalake>=12.14.0
azure-identity>=1.15.0
pyarrow>=14.0.0  # For Parquet reading
```

---

## Cost Impact

| Item | Monthly Cost |
|------|--------------|
| Azure Data Egress | ~$5-10 |
| Additional AWS Secrets | ~$0.40 |
| **Total Additional** | **~$5-11/month** |

---

## Open Questions

1. **Data Refresh Frequency:** How often should Gold layer be synced?
   - Real-time (Databricks streaming) vs Batch (daily/hourly)

2. **Historical Data:** Should we expose historical trends from Gold layer?
   - Requires additional storage consideration

3. **User Permissions:** Should data source toggle be admin-only?
   - Recommend: Yes, admin-only setting

---

## Next Steps

1. Get Azure SAS token with read permissions
2. Test Azure connectivity from AWS App Runner
3. Implement azure_data_service.py
4. Add UI toggle
5. Deploy and test
