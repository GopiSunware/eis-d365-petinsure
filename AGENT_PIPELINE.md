# Agent Pipeline & Rule Engine - Technical Deep Dive

## Overview

This platform has **two distinct claim processing pipelines**:

| Pipeline | Project | Technology | Purpose |
|----------|---------|------------|---------|
| **AI Agent Pipeline** | EIS Dynamics | LangGraph + Claude/GPT | AI-driven claim processing with reasoning |
| **Rule Engine Pipeline** | PetInsure360 | Databricks + Delta Lake | Traditional ETL with business rules |

Both follow the **Medallion Architecture** (Bronze → Silver → Gold), but with different implementations.

---

## 1. AI Agent Pipeline (EIS Dynamics)

### Architecture

```
                           ┌─────────────────────────────────────────────┐
                           │         LangGraph State Machine              │
                           └─────────────────────────────────────────────┘
                                              │
        ┌──────────────────┬──────────────────┼──────────────────┬──────────────────┐
        ▼                  ▼                  ▼                  ▼                  │
  ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐               │
  │  Router  │─────▶│  Bronze  │─────▶│  Silver  │─────▶│   Gold   │               │
  │  Agent   │      │  Agent   │      │  Agent   │      │  Agent   │               │
  └──────────┘      └──────────┘      └──────────┘      └──────────┘               │
        │                  │                  │                  │                  │
        │                  ▼                  ▼                  ▼                  │
        │           ┌──────────┐      ┌──────────┐      ┌──────────┐               │
        │           │ S3 Bronze│      │ S3 Silver│      │ S3 Gold  │               │
        │           │  Bucket  │      │  Bucket  │      │  Bucket  │               │
        │           └──────────┘      └──────────┘      └──────────┘               │
        │                                                                           │
        └───────────────────────────────────────────────────────────────────────────┘
                                    Conditional Edges
```

### Key Files

| File | Purpose |
|------|---------|
| `ws6_agent_pipeline/app/orchestration/pipeline.py` | Main LangGraph state machine |
| `ws6_agent_pipeline/app/agents/router_agent.py` | Determines claim complexity |
| `ws6_agent_pipeline/app/agents/bronze_agent.py` | Data validation & cleaning |
| `ws6_agent_pipeline/app/agents/silver_agent.py` | Enrichment & fraud detection |
| `ws6_agent_pipeline/app/agents/gold_agent.py` | Final decision & analytics |
| `ws6_agent_pipeline/app/orchestration/state.py` | State management |
| `ws6_agent_pipeline/app/orchestration/events.py` | WebSocket event publishing |

### How It Works

#### Step 1: Pipeline Initialization

```python
# pipeline.py - MedallionPipeline class
class MedallionPipeline:
    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(MedallionPipelineState)

        # Add agent nodes
        graph.add_node("router", self._router_node)
        graph.add_node("bronze", self._bronze_node)
        graph.add_node("silver", self._silver_node)
        graph.add_node("gold", self._gold_node)

        # Entry point
        graph.set_entry_point("router")

        # Conditional edges (can exit early if error/rejection)
        graph.add_conditional_edges("router", self._after_router, ...)
        graph.add_conditional_edges("bronze", self._after_bronze, ...)
        graph.add_conditional_edges("silver", self._after_silver, ...)
        graph.add_edge("gold", END)

        return graph.compile()
```

#### Step 2: Router Agent

The Router analyzes the claim and determines:
- **Complexity**: low, medium, high, critical
- **Processing Path**: standard, expedited, manual_review

```python
# router_agent.py
result = await router_agent.route(
    run_id=state.run_id,
    claim_id=state.claim_id,
    claim_data=state.claim_data,
)
# Returns: {"complexity": "medium", "processing_path": "standard"}
```

#### Step 3: Bronze Agent (Validation)

The Bronze Agent uses **LangGraph's ReAct pattern** with tools:

```python
# bronze_agent.py
class BronzeAgent:
    def __init__(self):
        self.tools = (
            BRONZE_VALIDATION_TOOLS +      # validate_schema, detect_anomalies, clean_data
            UNIFIED_API_BRONZE_TOOLS +     # get_policy, verify_provider
            [write_bronze, get_historical_claims]
        )
        self.llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
        self.agent = create_react_agent(self.llm, self.tools, prompt=BRONZE_AGENT_PROMPT)
```

**What Bronze Does:**
1. Validates schema (required fields, data types)
2. Detects anomalies (duplicate claims, unusual amounts)
3. Cleans data (normalize dates, provider names)
4. Calls `get_policy()` API to verify policy exists
5. Makes decision: **ACCEPT**, **QUARANTINE**, or **REJECT**
6. Writes output to S3 Bronze bucket

#### Step 4: Silver Agent (Enrichment)

The Silver Agent enriches data and performs fraud detection:

```python
# silver_agent.py
SILVER_AGENT_PROMPT = """You are a Silver Layer Enrichment Agent...
- Enrich claim with provider history
- Check for fraud patterns
- Calculate risk scores
- Cross-reference with historical data
"""
```

**What Silver Does:**
1. Enriches with policy details (coverage limits, deductibles)
2. Fraud pattern detection (chronic gaming, provider collusion)
3. Calculates preliminary risk score
4. Writes output to S3 Silver bucket

#### Step 5: Gold Agent (Decision)

The Gold Agent makes the final adjudication decision:

```python
# gold_agent.py
result = {
    "final_decision": "approve",  # approve, deny, review
    "fraud_score": 0.15,
    "risk_level": "low",
    "payout_amount": 450.00,
    "insights": ["Valid policy", "Provider verified", "No fraud indicators"],
}
```

**What Gold Does:**
1. Aggregates all layer outputs
2. Makes final decision with reasoning
3. Calculates payout amount
4. Generates analytics insights
5. Writes to S3 Gold bucket

### State Management

```python
# state.py - MedallionPipelineState
class MedallionPipelineState(BaseModel):
    run_id: str
    claim_id: str
    claim_data: dict
    current_stage: str = "trigger"

    # Agent outputs
    router_output: Optional[dict] = None
    bronze_output: Optional[dict] = None
    silver_output: Optional[dict] = None
    gold_output: Optional[dict] = None

    # Final results
    final_decision: str = "pending"
    fraud_score: float = 0.0
    risk_level: str = "unknown"
```

### Real-Time Events (WebSocket)

```python
# events.py
await event_publisher.publish_agent_started(run_id, claim_id, "bronze", total_steps=5)
await event_publisher.publish_step_completed(run_id, "Schema Validation", result)
await event_publisher.publish_agent_completed(run_id, claim_id, "bronze", output)
```

Frontend receives these via WebSocket for live pipeline visualization.

---

## 2. Rule Engine Pipeline (PetInsure360)

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Azure Databricks                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐          │
│   │ 01_bronze_      │────▶│ 02_silver_      │────▶│ 03_gold_        │          │
│   │ ingestion.py    │     │ transformations │     │ aggregations.py │          │
│   └────────┬────────┘     └────────┬────────┘     └────────┬────────┘          │
│            │                       │                       │                    │
│            ▼                       ▼                       ▼                    │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐          │
│   │  ADLS Bronze    │     │  ADLS Silver    │     │  ADLS Gold      │          │
│   │  Delta Tables   │     │  Delta Tables   │     │  Delta Tables   │          │
│   └─────────────────┘     └─────────────────┘     └─────────────────┘          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Parquet Exports
                                      ▼
                        ┌─────────────────────────────┐
                        │    gold/exports/            │
                        │  - customer_360/            │
                        │  - claims_analytics/        │
                        │  - monthly_kpis/            │
                        └─────────────────────────────┘
                                      │
                                      │ Read via AzureDataService
                                      ▼
                        ┌─────────────────────────────┐
                        │  AWS Claims-Data-API        │
                        │  (9wvcjmrknc.awsapprunner)  │
                        └─────────────────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `petinsure360/notebooks/01_bronze_ingestion.py` | Raw data → Bronze Delta tables |
| `petinsure360/notebooks/02_silver_transformations.py` | Bronze → Silver (cleaned) |
| `petinsure360/notebooks/03_gold_aggregations.py` | Silver → Gold (analytics) |
| `petinsure360/backend/app/services/insights.py` | Read Gold layer for API |
| `claims_data_api/app/services/azure_data_service.py` | AWS reads Azure Gold data |

### How It Works

#### Step 1: Bronze Ingestion (Databricks Notebook)

```python
# 01_bronze_ingestion.py

# Configuration
storage_account = "petinsud7i43"
bronze_path = f"abfss://bronze@{storage_account}.dfs.core.windows.net"
raw_path = f"abfss://raw@{storage_account}.dfs.core.windows.net"

# Create database
spark.sql("CREATE DATABASE IF NOT EXISTS petinsure_bronze")

# Helper: Add metadata columns
def add_bronze_metadata(df):
    return df \
        .withColumn("_ingestion_timestamp", current_timestamp()) \
        .withColumn("_source_file", input_file_name()) \
        .withColumn("_batch_id", lit(datetime.now().strftime("%Y%m%d%H%M%S")))

# Ingest customers CSV → Bronze Delta
df_customers = spark.read.csv(f"{raw_path}/customers.csv", header=True)
df_customers_bronze = add_bronze_metadata(df_customers)
df_customers_bronze.write.format("delta").saveAsTable("customers_raw")
```

**Bronze Tables Created:**
- `petinsure_bronze.customers_raw`
- `petinsure_bronze.pets_raw`
- `petinsure_bronze.policies_raw`
- `petinsure_bronze.claims_raw`
- `petinsure_bronze.vet_providers_raw`

#### Step 2: Silver Transformation

```python
# 02_silver_transformations.py

# Read Bronze
df_customers = spark.table("petinsure_bronze.customers_raw")

# Clean and validate
df_customers_clean = df_customers \
    .filter(col("customer_id").isNotNull()) \
    .filter(col("email").rlike("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")) \
    .withColumn("full_name", concat_ws(" ", col("first_name"), col("last_name")))

# Write to Silver
df_customers_clean.write.format("delta").saveAsTable("petinsure_silver.customers_clean")
```

#### Step 3: Gold Aggregation

```python
# 03_gold_aggregations.py

# Create Customer 360 view
df_customer_360 = spark.sql("""
    SELECT
        c.customer_id,
        c.full_name,
        c.customer_segment,
        COUNT(cl.claim_id) as total_claims,
        SUM(cl.claim_amount) as total_claim_amount,
        AVG(cl.claim_amount) as avg_claim_amount,
        SUM(p.annual_premium) as total_annual_premium,
        CASE WHEN SUM(p.annual_premium) > 0
             THEN SUM(cl.claim_amount) / SUM(p.annual_premium)
             ELSE 0 END as loss_ratio
    FROM petinsure_silver.customers_clean c
    LEFT JOIN petinsure_silver.claims_validated cl ON c.customer_id = cl.customer_id
    LEFT JOIN petinsure_silver.policies_clean p ON c.customer_id = p.customer_id
    GROUP BY c.customer_id, c.full_name, c.customer_segment
""")

df_customer_360.write.format("delta").saveAsTable("petinsure_gold.customer_360")

# Export as Parquet for API consumption
df_customer_360.write.parquet("abfss://gold@petinsud7i43.dfs.core.windows.net/exports/customer_360/")
```

### How AWS Reads Azure Data

```python
# claims_data_api/app/services/azure_data_service.py

class AzureDataService:
    def __init__(self):
        self.storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
        self.storage_key = os.getenv("AZURE_STORAGE_KEY")

    async def get_customer_360(self) -> List[dict]:
        """Read Customer 360 from Azure Gold layer."""
        path = "gold/exports/customer_360/"
        df = pd.read_parquet(
            f"abfss://{path}@{self.storage_account}.dfs.core.windows.net/",
            storage_options={"account_key": self.storage_key}
        )
        return df.to_dict(orient="records")
```

---

## 3. Key Differences

| Aspect | AI Agent Pipeline | Rule Engine Pipeline |
|--------|-------------------|---------------------|
| **Technology** | LangGraph + LLM | Databricks + PySpark |
| **Processing** | Real-time, per-claim | Batch ETL |
| **Decision Making** | AI reasoning with tools | SQL transformations |
| **Explainability** | Natural language reasoning | Query-based rules |
| **Flexibility** | Handles edge cases | Fixed business rules |
| **Cost** | LLM API costs | Databricks compute |
| **Speed** | ~2-5 sec per claim | Minutes for batch |
| **Storage** | AWS S3 | Azure ADLS Gen2 |

---

## 4. Triggering the Pipelines

### AI Agent Pipeline (EIS Dynamics)

```bash
# Via API
curl -X POST https://qi2p3x5gsm.us-east-1.awsapprunner.com/api/v1/pipeline/process \
  -H "Content-Type: application/json" \
  -d '{"claim_id": "CLM-001", "claim_data": {...}}'

# Via Agent Portal UI
# Navigate to: http://eis-agent-portal.s3-website-us-east-1.amazonaws.com/pipeline
# Click "Process Claim" button
```

### Rule Engine Pipeline (PetInsure360)

```bash
# Option 1: Run Databricks notebooks manually
# Azure Portal → Databricks Workspace → Workflows → Run Job

# Option 2: Via BI Dashboard API
curl -X POST https://fucf3fwwwv.us-east-1.awsapprunner.com/api/pipeline/process/bronze-to-silver

# Option 3: Via BI Dashboard UI
# Navigate to: http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com
# Click "Rule Engine Pipeline" → Process Bronze/Silver/Gold buttons
```

---

## 5. Monitoring

### AI Agent Pipeline

```bash
# Pipeline status
curl https://qi2p3x5gsm.us-east-1.awsapprunner.com/api/v1/pipeline/status

# Individual run details
curl https://qi2p3x5gsm.us-east-1.awsapprunner.com/api/v1/pipeline/runs/{run_id}

# WebSocket for real-time updates
wscat -c wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod
```

### Rule Engine Pipeline

```bash
# Pipeline flow status
curl https://fucf3fwwwv.us-east-1.awsapprunner.com/api/pipeline/flow

# Pending claims per layer
curl https://fucf3fwwwv.us-east-1.awsapprunner.com/api/pipeline/pending

# Databricks: Check job runs in Azure Portal
# Azure Portal → Databricks Workspace → Workflows → Job Runs
```

---

## 6. Data Flow Summary

```
                    CLAIM SUBMISSION
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
     ┌──────────────┐           ┌──────────────┐
     │ EIS Portal   │           │ PetInsure360 │
     │ (Agent)      │           │ (Customer)   │
     └──────┬───────┘           └──────┬───────┘
            │                          │
            ▼                          ▼
     ┌──────────────┐           ┌──────────────┐
     │ Agent        │           │ Azure ADLS   │
     │ Pipeline     │           │ Raw Layer    │
     │ (LangGraph)  │           └──────┬───────┘
     └──────┬───────┘                  │
            │                          ▼
            ▼                   ┌──────────────┐
     ┌──────────────┐           │ Databricks   │
     │ S3 Data Lake │           │ Notebooks    │
     │ (Medallion)  │           │ (Bronze→Gold)│
     └──────┬───────┘           └──────┬───────┘
            │                          │
            ▼                          ▼
     ┌──────────────┐           ┌──────────────┐
     │ Real-time    │           │ Gold Layer   │
     │ Decision     │           │ Analytics    │
     └──────────────┘           └──────────────┘
```
