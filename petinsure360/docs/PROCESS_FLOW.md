# PetInsure360 - Medallion Lakehouse Process Flow

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          PETINSURE360 - END TO END DATA FLOW                             │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────────────────────────────────┐  │
│  │  CUSTOMER   │      │   BACKEND   │      │           AZURE DATA LAKE GEN2          │  │
│  │   PORTAL    │─────►│    API      │─────►│              (petinsud7i43)              │  │
│  │   (React)   │      │  (FastAPI)  │      │                                         │  │
│  └─────────────┘      └─────────────┘      │  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐│
│                                            │  │  RAW  │  │BRONZE │  │SILVER │  │ GOLD  ││
│                                            │  │       │  │       │  │       │  │       ││
│                                            │  │ JSON  │  │ DELTA │  │ DELTA │  │ DELTA ││
│                                            │  │  CSV  │  │ LAKE  │  │ LAKE  │  │ LAKE  ││
│                                            │  └───┬───┘  └───┬───┘  └───┬───┘  └───┬───┘│
│                                            └──────┼──────────┼──────────┼──────────┼────┘│
│                                                   │          │          │          │     │
│                                                   ▼          ▼          ▼          ▼     │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           AZURE DATABRICKS                                          │ │
│  │                    (petinsure360-databricks-dev)                                    │ │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐                  │ │
│  │  │ 01_bronze_       │  │ 02_silver_       │  │ 03_gold_         │                  │ │
│  │  │ ingestion.py     │─►│ transformations  │─►│ aggregations.py  │                  │ │
│  │  │                  │  │ .py              │  │                  │                  │ │
│  │  │ • Read CSV/JSON  │  │ • Clean data     │  │ • Aggregate      │                  │ │
│  │  │ • Add metadata   │  │ • Validate       │  │ • Join dims      │                  │ │
│  │  │ • Write Delta    │  │ • Deduplicate    │  │ • Calc KPIs      │                  │ │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘                  │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                   │                                      │
│                                                   ▼                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                         AZURE SYNAPSE ANALYTICS                                     │ │
│  │                         (petins-syn-ud7i43)                                         │ │
│  │  ┌────────────────────────────────────────────────────────────────────────────┐    │ │
│  │  │ Serverless SQL Pool - Query Delta Tables Directly                          │    │ │
│  │  │ • vw_customer_360       • vw_claims_analytics    • vw_monthly_kpis        │    │ │
│  │  │ • vw_risk_scoring       • vw_cross_sell          • vw_provider_performance│    │ │
│  │  └────────────────────────────────────────────────────────────────────────────┘    │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                   │                                      │
│                                                   ▼                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                              BI DASHBOARD                                           │ │
│  │  • Power BI (DirectQuery to Synapse)                                               │ │
│  │  • React Dashboard (API → Synapse)                                                 │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Delta Lake Features (DEMO POINTS)

### What is Delta Lake?

Delta Lake is an open-source storage layer that brings ACID transactions to Apache Spark and big data workloads.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DELTA LAKE FEATURES                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. ACID TRANSACTIONS                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Atomicity   - All or nothing writes                               │    │
│  │ • Consistency - Data always valid                                   │    │
│  │ • Isolation   - Concurrent reads/writes                             │    │
│  │ • Durability  - Committed data persists                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  2. TIME TRAVEL (Version History)                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ -- Query data as of specific version                                │    │
│  │ SELECT * FROM customers VERSION AS OF 5;                            │    │
│  │                                                                     │    │
│  │ -- Query data as of timestamp                                       │    │
│  │ SELECT * FROM customers TIMESTAMP AS OF '2024-01-01';               │    │
│  │                                                                     │    │
│  │ -- Restore to previous version                                      │    │
│  │ RESTORE TABLE customers TO VERSION AS OF 3;                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  3. SCHEMA ENFORCEMENT & EVOLUTION                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Prevents bad data from corrupting tables                          │    │
│  │ • Automatically evolve schema with new columns                      │    │
│  │ • .option("mergeSchema", "true")                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  4. UNIFIED BATCH & STREAMING                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Same table for batch and streaming workloads                      │    │
│  │ • Exactly-once processing guarantees                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  5. AUDIT HISTORY                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ DESCRIBE HISTORY customers;                                         │    │
│  │                                                                     │    │
│  │ version | timestamp           | operation | userName               │    │
│  │ 0       | 2024-01-01 10:00:00 | CREATE    | admin@company.com      │    │
│  │ 1       | 2024-01-02 14:30:00 | WRITE     | etl_service            │    │
│  │ 2       | 2024-01-03 09:15:00 | UPDATE    | etl_service            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Delta Lake Demo Commands (Databricks)

```python
# Show table history (Time Travel)
%sql
DESCRIBE HISTORY petinsure_gold.customer_360;

# Query previous version
%sql
SELECT * FROM petinsure_gold.customer_360 VERSION AS OF 1;

# Compare versions
%sql
SELECT
    'Current' as version,
    COUNT(*) as record_count,
    SUM(total_claim_amount) as total_claims
FROM petinsure_gold.customer_360
UNION ALL
SELECT
    'Previous' as version,
    COUNT(*) as record_count,
    SUM(total_claim_amount) as total_claims
FROM petinsure_gold.customer_360 VERSION AS OF 1;

# Show table details
%sql
DESCRIBE DETAIL petinsure_gold.customer_360;
```

---

## Data Lineage (DEMO POINTS)

### What is Data Lineage?

Data lineage tracks the complete journey of data from source to destination, showing all transformations applied.

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              DATA LINEAGE FLOW                                           │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  SOURCE DATA                 BRONZE                  SILVER                  GOLD        │
│  (Raw Files)                 (As-Is + Metadata)      (Cleaned)              (Analytics)  │
│                                                                                          │
│  ┌──────────────┐           ┌──────────────┐        ┌──────────────┐       ┌──────────┐ │
│  │customers.csv │──────────►│customers_raw │───────►│dim_customers │──────►│customer_ │ │
│  │              │           │              │        │              │       │360_view  │ │
│  │ • 5000 rows  │           │ • +metadata  │        │ • validated  │       │          │ │
│  │ • 19 columns │           │ • +timestamp │        │ • deduped    │       │ • joined │ │
│  └──────────────┘           │ • +source    │        │ • typed      │       │ • aggreg │ │
│                             └──────────────┘        └──────────────┘       └──────────┘ │
│                                                                                          │
│  ┌──────────────┐           ┌──────────────┐        ┌──────────────┐            │       │
│  │  pets.csv    │──────────►│  pets_raw    │───────►│  dim_pets    │────────────┤       │
│  │              │           │              │        │              │            │       │
│  │ • 6500 rows  │           │ • +metadata  │        │ • validated  │            │       │
│  └──────────────┘           └──────────────┘        └──────────────┘            │       │
│                                                                                  │       │
│  ┌──────────────┐           ┌──────────────┐        ┌──────────────┐            │       │
│  │policies.csv  │──────────►│policies_raw  │───────►│dim_policies  │────────────┤       │
│  │              │           │              │        │              │            │       │
│  │ • 6000 rows  │           │ • +metadata  │        │ • validated  │            ▼       │
│  └──────────────┘           └──────────────┘        └──────────────┘       ┌──────────┐ │
│                                                                            │ monthly_ │ │
│  ┌──────────────┐           ┌──────────────┐        ┌──────────────┐       │ kpis     │ │
│  │claims.jsonl  │──────────►│ claims_raw   │───────►│fact_claims   │──────►│          │ │
│  │              │           │              │        │              │       │ claims_  │ │
│  │ • 15000 rows │           │ • +metadata  │        │ • validated  │       │ analytics│ │
│  └──────────────┘           │ • +quality   │        │ • enriched   │       │          │ │
│                             └──────────────┘        └──────────────┘       │ risk_    │ │
│                                                                            │ scoring  │ │
│  ┌──────────────┐           ┌──────────────┐        ┌──────────────┐       │          │ │
│  │providers.csv │──────────►│providers_raw │───────►│dim_providers │──────►│ cross_   │ │
│  │              │           │              │        │              │       │ sell     │ │
│  │ • 200 rows   │           │ • +metadata  │        │ • validated  │       └──────────┘ │
│  └──────────────┘           └──────────────┘        └──────────────┘                    │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Lineage Tracking in Each Layer

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BRONZE LAYER - METADATA COLUMNS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Original Data Columns                                                       │
│  ─────────────────────                                                       │
│  customer_id, first_name, last_name, email, phone, ...                      │
│                                                                              │
│  + Lineage Metadata (Added by ETL)                                           │
│  ─────────────────────────────────                                           │
│  _ingestion_timestamp  │ When data was ingested    │ 2024-01-15T10:30:00    │
│  _source_file          │ Original source file      │ raw/customers.csv      │
│  _batch_id             │ ETL batch identifier      │ 20240115103000         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    SILVER LAYER - QUALITY COLUMNS                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Bronze Columns (inherited)                                                  │
│  ──────────────────────────                                                  │
│  All bronze columns + metadata                                               │
│                                                                              │
│  + Quality Metadata (Added by ETL)                                           │
│  ─────────────────────────────────                                           │
│  _silver_processed_at  │ Silver processing time   │ 2024-01-15T11:00:00     │
│  _is_valid             │ Passed validation        │ true/false              │
│  _quality_score        │ Data quality score       │ 95.5                    │
│  _is_duplicate         │ Duplicate record flag    │ true/false              │
│  _duplicate_of         │ Original record ID       │ null or customer_id     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    GOLD LAYER - BUSINESS COLUMNS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Business Aggregations                                                       │
│  ─────────────────────                                                       │
│  customer_id, full_name, total_pets, total_policies, total_claims,          │
│  total_claim_amount, loss_ratio, customer_value_tier, risk_score            │
│                                                                              │
│  + Lineage Metadata                                                          │
│  ──────────────────                                                          │
│  _gold_processed_at    │ Gold processing time     │ 2024-01-15T12:00:00     │
│  _source_tables        │ Source silver tables     │ [dim_customers, ...]    │
│  _aggregation_type     │ Type of aggregation      │ customer_360            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Viewing Lineage in Databricks

```python
# View column-level lineage
%sql
SELECT
    table_name,
    column_name,
    data_type,
    comment
FROM information_schema.columns
WHERE table_schema = 'petinsure_gold';

# View table dependencies (Unity Catalog)
%sql
SHOW TABLE EXTENDED IN petinsure_gold LIKE '*';

# Custom lineage query
%sql
SELECT DISTINCT
    _source_file as source,
    'bronze' as layer,
    COUNT(*) as records
FROM petinsure_bronze.customers_raw
GROUP BY _source_file;
```

---

## Demo Flow Script

### Step-by-Step Demo Walkthrough

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DEMO SCRIPT (30 minutes)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PART 1: Customer Portal (5 min)                                             │
│  ────────────────────────────────                                            │
│  1. Open https://petinsure360frontend.z5.web.core.windows.net               │
│  2. Login as demo1@demologin.com                                            │
│  3. Submit a new claim using scenario dropdown                              │
│  4. Show real-time WebSocket notification                                   │
│  5. Show claim appears in Claims page                                       │
│                                                                              │
│  PART 2: Data Lake (5 min)                                                   │
│  ────────────────────────                                                    │
│  1. Open Azure Portal → Storage Account (petinsud7i43)                      │
│  2. Show containers: raw, bronze, silver, gold                              │
│  3. Navigate to raw/claims/ → Show new claim JSON file                      │
│  4. Explain: "Raw data lands here immediately"                              │
│                                                                              │
│  PART 3: Databricks ETL (10 min)                                             │
│  ───────────────────────────────                                             │
│  1. Open https://adb-7405619408519767.7.azuredatabricks.net                 │
│  2. Navigate to Workspace → Shared → PetInsure360                           │
│  3. Run 01_bronze_ingestion notebook                                        │
│     - Show: Raw files → Delta tables                                        │
│     - Show: Metadata columns added (_ingestion_timestamp, _source_file)     │
│  4. Run 02_silver_transformations notebook                                  │
│     - Show: Data validation and cleaning                                    │
│     - Show: Quality scores calculated                                       │
│  5. Run 03_gold_aggregations notebook                                       │
│     - Show: Business aggregations (Customer 360, KPIs)                      │
│     - Show: Delta Lake features:                                            │
│       * DESCRIBE HISTORY customer_360                                       │
│       * Time travel query                                                   │
│                                                                              │
│  PART 4: Synapse Analytics (5 min)                                           │
│  ─────────────────────────────────                                           │
│  1. Open Synapse Studio (web.azuresynapse.net)                              │
│  2. Navigate to Data → External Tables                                      │
│  3. Run SQL query:                                                          │
│     SELECT * FROM vw_customer_360 WHERE customer_id = 'DEMO-002'            │
│  4. Show: Serverless SQL queries Delta Lake directly                        │
│  5. Explain: "Power BI connects here for real-time dashboards"              │
│                                                                              │
│  PART 5: Data Lineage (5 min)                                                │
│  ────────────────────────────                                                │
│  1. Back in Databricks, show:                                               │
│     %sql DESCRIBE HISTORY petinsure_gold.customer_360;                      │
│  2. Show audit trail of all changes                                         │
│  3. Query previous version:                                                 │
│     SELECT * FROM customer_360 VERSION AS OF 1;                             │
│  4. Explain: "Complete audit trail, can restore any version"               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Azure Service URLs (Quick Reference)

| Service | URL | Status |
|---------|-----|--------|
| **Customer Portal** | https://petinsure360frontend.z5.web.core.windows.net | LIVE |
| **Backend API** | https://petinsure360-backend.azurewebsites.net | LIVE |
| **Databricks** | https://adb-7405619408519767.7.azuredatabricks.net | LIVE |
| **Databricks Cluster** | PetInsure360-Demo-v2 (ID: 0101-204045-2fdc7837) | RUNNING |
| **Synapse Studio** | https://web.azuresynapse.net | Ready for Views |
| **Data Factory** | https://adf.azure.com | Available |
| **Azure Portal** | https://portal.azure.com | - |

### ETL Status (As of 2026-01-01)

| Layer | Status | Records | Location |
|-------|--------|---------|----------|
| **Raw** | Source Data | 45 files | `raw/` container |
| **Bronze** | ETL Complete | 5 tables | Databricks Metastore |
| **Silver** | ETL Complete | 5 tables | Databricks Metastore |
| **Gold** | ETL Complete | 6 tables | `gold/` container (Delta) |

### Gold Delta Tables in ADLS

| Table | Path | Purpose |
|-------|------|---------|
| customer_360_view | gold/customer_360_view | CDP unified customer view |
| claims_analytics | gold/claims_analytics | Detailed claims analysis |
| monthly_kpis | gold/monthly_kpis | Executive dashboard metrics |
| cross_sell_recommendations | gold/cross_sell_recommendations | Upsell opportunities |
| provider_performance | gold/provider_performance | Vet network analytics |
| risk_scoring | gold/risk_scoring | Customer risk assessment |

---

## Key Talking Points for Client Demo

### 1. Medallion Architecture
> "Data flows through Bronze (raw), Silver (cleaned), Gold (analytics) - each layer adds value and quality."

### 2. Delta Lake
> "Delta Lake gives us ACID transactions, time travel for auditing, and schema enforcement - enterprise-grade reliability on cloud storage."

### 3. Data Lineage
> "We track every transformation from source to dashboard. Full audit trail for compliance and debugging."

### 4. Serverless Analytics
> "Synapse serverless means we only pay when queries run - no always-on infrastructure costs."

### 5. Real-time + Batch
> "Claims submitted in the portal land in the lake immediately. ETL runs on schedule or on-demand."

---

## Cost Optimization Notes

| Service | Billing Model | Optimization |
|---------|---------------|--------------|
| Databricks | Per DBU-hour | Use spot instances, auto-terminate clusters |
| Synapse | Per TB scanned | Use partitioning, query only needed columns |
| Storage | Per GB stored | Use lifecycle policies, archive old data |
| Data Factory | Per activity run | Batch small files, optimize pipeline design |

---

*Document Version: 1.0*
*Author: Sunware Technologies*
*Last Updated: 2026-01-01*
