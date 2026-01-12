# Agent Pipeline & Rule Engine - Technical Deep Dive

## Overview

This platform has **two distinct claim processing pipelines**:

| Pipeline | Project | Technology | Purpose |
|----------|---------|------------|---------|
| **AI Agent Pipeline** | EIS Dynamics | LangGraph + Claude/GPT | AI-driven claim processing with reasoning |
| **Rule Engine Pipeline** | PetInsure360 | Databricks + Delta Lake | Traditional ETL with business rules |

Both follow the **Medallion Architecture** (Bronze → Silver → Gold), but with different implementations.

---

## Storage Separation (IMPORTANT)

**The two pipelines write to DIFFERENT storage backends:**

| Pipeline | Storage | Account/Bucket | Paths |
|----------|---------|----------------|-------|
| **AI Agent Pipeline** | AWS S3 | `eis-dynamics-datalake-611670815873` | `bronze/`, `silver/`, `gold/` |
| **Rule Engine Pipeline** | Azure ADLS Gen2 | `petinsud7i43` | `bronze/`, `silver/`, `gold/` |

### Why Different Storage?

1. **Agent Pipeline (EIS Dynamics)**: Runs on AWS App Runner, uses S3 for real-time per-claim outputs
2. **Rule Engine (PetInsure360)**: Runs on Azure Databricks, uses ADLS for batch Delta Lake tables

### Storage Code References

**Agent Pipeline → S3:**
```python
# ws6_agent_pipeline/app/services/s3_service.py
class S3DataLakeService:
    def __init__(self):
        self.bucket_name = os.getenv("S3_DATALAKE_BUCKET", "eis-dynamics-datalake-611670815873")

    def write_bronze_output(self, claim_id: str, run_id: str, bronze_data: Dict):
        key = f"bronze/{claim_id}/output.json"
        self.s3_client.put_object(Bucket=self.bucket_name, Key=key, Body=json.dumps(bronze_data))
```

**Rule Engine → Azure ADLS:**
```python
# petinsure360/notebooks/01_bronze_ingestion.py
storage_account = "petinsud7i43"
bronze_path = f"abfss://bronze@{storage_account}.dfs.core.windows.net"
df_customers_bronze.write.format("delta").mode("overwrite").saveAsTable("customers_raw")
```

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

## Agent Prompts (Complete Reference)

### Router Agent (No LLM - Rule-Based)

The Router Agent does **NOT** use an LLM. It uses rule-based logic:

```python
# router_agent.py - Rule-based complexity assessment
class RouterAgent:
    def __init__(self):
        self.amount_thresholds = {"simple": 1000, "medium": 10000, "complex": float("inf")}
        self.complex_claim_types = ["emergency", "surgery", "hospitalization"]
        self.simple_claim_types = ["wellness", "routine", "vaccination"]

    def _assess_complexity(self, claim_data: dict) -> str:
        amount = claim_data.get("claim_amount", 0)
        claim_type = claim_data.get("claim_type", "").lower()

        # Amount-based assessment
        if amount <= self.amount_thresholds["simple"]:
            complexity = "low"
        elif amount <= self.amount_thresholds["medium"]:
            complexity = "medium"
        else:
            complexity = "high"

        # Claim type adjustment
        if claim_type in self.complex_claim_types:
            complexity = "high" if complexity != "critical" else complexity
        elif claim_type in self.simple_claim_types:
            complexity = "low"

        return complexity
```

### Bronze Agent Prompt

```python
BRONZE_AGENT_PROMPT = """You are a Bronze Layer Data Agent specializing in data validation and quality assurance.

Your job is to validate and clean incoming pet insurance claim data.

## YOUR TOOLS:
- validate_schema: Check all required fields are present and correctly typed
- detect_anomalies: Look for suspicious patterns in the data
- clean_data: Normalize and fix data issues
- get_policy: Fetch policy details from the unified API
- verify_provider: Verify the veterinary provider is licensed
- write_bronze: Write validated data to the Bronze layer
- get_historical_claims: Get past claims for comparison

## YOUR WORKFLOW:
1. **VALIDATE**: Check all required fields are present and correctly typed
2. **DETECT ANOMALIES**: Look for suspicious patterns:
   - Duplicate claim submissions
   - Unusual claim amounts (too high or too low)
   - Mismatched dates (treatment before policy start)
   - Invalid diagnosis codes
3. **CLEAN**: Normalize and fix data issues:
   - Standardize date formats
   - Normalize provider names
   - Fix common typos in diagnosis codes
4. **ASSESS QUALITY**: Rate the overall data quality (0-100)
5. **DECIDE**: Make a decision about this claim:
   - ACCEPT: Data is valid and ready for Silver layer processing
   - QUARANTINE: Data has issues that need human review
   - REJECT: Data is invalid and cannot be processed

Always explain your reasoning clearly.
"""
```

### Silver Agent Prompt

```python
SILVER_AGENT_PROMPT = """You are a Silver Layer Enrichment Agent specializing in data enrichment and fraud detection.

Your job is to enrich validated claim data with additional context and perform initial fraud screening.

## YOUR TOOLS:
- get_customer: Fetch customer profile and history
- get_claim_history: Get the customer's past claims
- get_pet_medical_history: Get the pet's full medical history
- get_pet_pre_existing_conditions: Get known pre-existing conditions for the pet
- check_coverage: Verify the treatment is covered by the policy
- calculate_reimbursement: Calculate the expected reimbursement amount
- write_silver: Write enriched data to the Silver layer

## YOUR WORKFLOW:
1. **ENRICH**: Add customer and policy context
2. **VALIDATE COVERAGE**: Check if the treatment is covered
3. **CHECK PRE-EXISTING CONDITIONS**:
   - **IMPORTANT**: Check pre-existing conditions - customers may claim "accidents" for chronic issues
   - Compare current diagnosis with pet's medical history
   - Flag if diagnosis matches a known pre-existing condition
4. **CALCULATE**: Determine reimbursement based on coverage
5. **ASSESS RISK**: Provide preliminary risk assessment

## FRAUD PATTERNS TO WATCH:
- Claims for "accidents" that match chronic condition symptoms
- Treatment dates that don't align with policy coverage
- Claims exceeding typical costs for the diagnosis
- Frequent claims for the same condition labeled differently

Always provide detailed reasoning for risk assessments.
"""
```

### Gold Agent Prompt (Primary Fraud Detection)

```python
GOLD_AGENT_PROMPT = """You are a Gold Layer Analytics Agent specializing in fraud detection and final claim adjudication.

**CRITICAL**: You have access to fraud detection tools that can identify patterns rule-based systems miss.

## YOUR TOOLS:
- check_fraud_indicators: Analyze claim for known fraud patterns
- velocity_check: Check claim frequency and timing patterns
- duplicate_check: Look for duplicate or similar claims
- fraud_pattern_match: Match against known fraud scenarios
- calculate_fraud_score: Generate overall fraud risk score (0-100)
- write_gold: Write final decision to Gold layer

## FRAUD PATTERNS TO DETECT:

### 1. Chronic Condition Gaming (e.g., CUST-023)
- Customer claims accident/injury for what is actually a chronic condition
- Signs: History of same symptoms, diagnosis progression, breed-specific conditions
- Example: Labrador with "accidental ligament tear" but history shows hip dysplasia

### 2. Provider Collusion (e.g., CUST-067)
- Customer exclusively uses out-of-network providers with inflated costs
- Signs: Always same provider, costs 40%+ above market, round-number billing
- Example: All claims from "Premier Pet Care" at 2x normal prices

### 3. Staged Timing (e.g., CUST-089)
- Claims submitted strategically just after waiting periods end
- Signs: Major claim within 30 days of waiting period, policy age correlations
- Example: $15,000 surgery claim on day 31 of policy

## YOUR WORKFLOW:
1. **ANALYZE**: Run all fraud detection tools
2. **CORRELATE**: Cross-reference findings from Bronze and Silver layers
3. **SCORE**: Calculate final fraud score (0-100)
4. **DECIDE**: Make final decision based on score:
   - AUTO_APPROVE: Low risk (score <25), claim amount ≤$500
   - STANDARD_REVIEW: Medium risk (score 25-49)
   - MANUAL_REVIEW: High risk (score 50-74)
   - INVESTIGATION: Critical risk (score ≥75) - escalate to fraud unit

## MAKE FINAL DECISION:
Always provide:
- Final decision (approve/deny/review/investigate)
- Fraud score with breakdown
- Key risk factors identified
- Recommended payout amount (if approved)
- Detailed reasoning for the decision
"""
```

---

## Issue Detection: Which Layer Detects What

| Layer | Issues Detected | How |
|-------|-----------------|-----|
| **Router** | Claim complexity | Rule-based amount/type thresholds |
| **Bronze** | Data quality issues | Schema validation, anomaly detection |
| **Bronze** | Missing/invalid fields | `validate_schema` tool |
| **Bronze** | Duplicate submissions | `detect_anomalies` tool |
| **Bronze** | Invalid provider | `verify_provider` tool |
| **Silver** | Coverage issues | `check_coverage` tool |
| **Silver** | Pre-existing conditions | `get_pet_pre_existing_conditions` tool |
| **Silver** | Cost anomalies | Reimbursement calculation vs claim |
| **Gold** | **Fraud patterns** | `check_fraud_indicators`, `fraud_pattern_match` |
| **Gold** | Velocity abuse | `velocity_check` tool |
| **Gold** | Duplicate claims | `duplicate_check` tool |

### Bronze Layer Detection

```python
# Example: Anomaly Detection
anomalies = [
    {"type": "duplicate_claim", "severity": "high", "details": "Claim ID matches previous submission"},
    {"type": "amount_outlier", "severity": "medium", "details": "Claim amount 3x typical for diagnosis"},
    {"type": "date_mismatch", "severity": "high", "details": "Treatment date before policy start"},
]
```

### Silver Layer Detection

```python
# Example: Pre-existing Condition Check
pre_existing_check = {
    "has_pre_existing": True,
    "condition": "Hip Dysplasia",
    "first_diagnosed": "2024-03-15",
    "current_claim_diagnosis": "Accidental Ligament Injury",
    "risk_flag": "POSSIBLE_CHRONIC_GAMING",
    "similarity_score": 0.85
}
```

### Gold Layer Detection (Main Fraud Detection)

```python
# Example: Fraud Pattern Match
fraud_analysis = {
    "fraud_score": 78,
    "risk_level": "high",
    "patterns_detected": [
        {
            "pattern": "CHRONIC_GAMING",
            "confidence": 0.85,
            "evidence": ["History of hip issues", "Same symptoms as pre-existing"]
        },
        {
            "pattern": "STAGED_TIMING",
            "confidence": 0.72,
            "evidence": ["Claim on day 32 of policy", "High-value procedure"]
        }
    ],
    "recommendation": "INVESTIGATION",
    "reasoning": "Multiple fraud indicators present with high confidence"
}
```

---

## Rule vs Agent Comparison Tab

The **Comparison** feature in the Agent Portal runs **BOTH** processing methods on the same claim and compares results.

### How It Works

```python
# comparison.py - /api/v1/comparison/run endpoint
@router.post("/run")
async def run_comparison(claim_data: dict[str, Any]):
    # Run BOTH processors in parallel
    code_task = asyncio.create_task(code_processor.process_claim(claim_data))
    agent_task = asyncio.create_task(medallion_pipeline.process_claim(claim_data))

    code_result, agent_result = await asyncio.gather(code_task, agent_task)

    return {
        "code_driven": {
            "decision": code_result["decision"],
            "processing_time_ms": code_result["processing_time"],
            "risk_level": code_result["risk_level"],
            # No reasoning - just deterministic rules
        },
        "agent_driven": {
            "decision": agent_result["final_decision"],
            "processing_time_ms": agent_result["processing_time"],
            "risk_level": agent_result["risk_level"],
            "reasoning_log": agent_result["reasoning"],  # AI explains why
            "insights": agent_result["insights"],         # AI-generated insights
        },
        "comparison_metrics": {
            "decision_match": code_result["decision"] == agent_result["decision"],
            "time_difference_ms": agent_time - code_time,
            "agent_advantages": [
                "Provides reasoning for decisions",
                "Generates actionable insights",
                "Adapts to edge cases and novel scenarios",
                "Detects complex fraud patterns"
            ],
            "code_advantages": [
                "Faster processing (~100ms vs ~3-5s)",
                "Deterministic and reproducible",
                "No API costs",
                "Easier to audit and debug"
            ]
        }
    }
```

### Use Case: Why Compare?

| Scenario | Best Choice |
|----------|-------------|
| High-volume, low-risk claims | Code-driven (speed, cost) |
| Complex fraud detection | Agent-driven (pattern recognition) |
| Audit/compliance needs | Code-driven (deterministic) |
| Customer disputes | Agent-driven (reasoning/explanation) |
| Edge cases | Agent-driven (adaptability) |

### Example Comparison Output

```json
{
  "claim_id": "CLM-2024-001",
  "code_driven": {
    "decision": "APPROVE",
    "processing_time_ms": 145,
    "risk_level": "low",
    "payout": 450.00
  },
  "agent_driven": {
    "decision": "MANUAL_REVIEW",
    "processing_time_ms": 3200,
    "risk_level": "medium",
    "payout": 450.00,
    "reasoning": "While the claim amount is low and data is valid, I detected a pattern: this customer has submitted 3 similar 'accident' claims in 6 months for the same body area. This warrants human review.",
    "insights": [
      "Customer claim frequency above average",
      "Same diagnosis category as previous claims",
      "Consider fraud investigation if pattern continues"
    ]
  },
  "comparison_metrics": {
    "decision_match": false,
    "code_missed_pattern": true
  }
}
```

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
| **Technology** | LangGraph + LLM (Claude/GPT) | Databricks + PySpark |
| **Processing** | Real-time, per-claim | Batch ETL |
| **Decision Making** | AI reasoning with tools | SQL transformations |
| **Explainability** | Natural language reasoning | Query-based rules |
| **Flexibility** | Handles edge cases, detects novel fraud | Fixed business rules |
| **Fraud Detection** | AI pattern matching (3 patterns) | Rule-based thresholds |
| **Cost** | LLM API costs (~$0.01-0.05/claim) | Databricks compute |
| **Speed** | ~2-5 sec per claim | Minutes for batch |
| **Storage** | **AWS S3** (`eis-dynamics-datalake-*`) | **Azure ADLS Gen2** (`petinsud7i43`) |
| **Data Format** | JSON files | Delta Lake tables |

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


  1. Storage Separation Section (NEW)

  - Agent Pipeline → AWS S3 (eis-dynamics-datalake-611670815873)
  - Rule Engine → Azure ADLS Gen2 (petinsud7i43)
  - Includes code references showing where each writes

  2. Complete Agent Prompts (NEW)

  - Router Agent: No LLM - rule-based complexity assessment (amount thresholds, claim types)
  - Bronze Agent Prompt: Schema validation, anomaly detection, data cleaning
  - Silver Agent Prompt: Enrichment, coverage validation, pre-existing condition checks
  - Gold Agent Prompt: Full fraud detection with 3 patterns (chronic gaming, provider collusion, staged timing)

  3. Issue Detection Table (NEW)

  Shows which layer detects what:
  ┌────────┬───────────────────────────────────────────────────────┐
  │ Layer  │                        Detects                        │
  ├────────┼───────────────────────────────────────────────────────┤
  │ Bronze │ Data quality, schema issues, duplicates               │
  ├────────┼───────────────────────────────────────────────────────┤
  │ Silver │ Coverage issues, pre-existing conditions              │
  ├────────┼───────────────────────────────────────────────────────┤
  │ Gold   │ Main fraud detection (patterns, velocity, duplicates) │
  └────────┴───────────────────────────────────────────────────────┘
  4. Rule vs Agent Comparison Tab (NEW)

  - Runs BOTH code-driven and agent-driven processing in parallel
  - Compares: decisions, times, risk levels
  - Agent provides reasoning/insights, code is faster/deterministic
  - Use case table showing when to use each

  Key Answers to Your Questions:

  1. Storage: YES, different - Agent→S3, Rule Engine→Azure ADLS
  2. Issue Detection: Gold layer is the primary fraud detector with 3 specific patterns
  3. Prompts: All now documented with full text
  4. Rule vs Agent tab: Parallel comparison showing tradeoffs


  

● The Rule vs Agent Comparison Tab in the Agent Portal lets you run the same claim through both processing methods simultaneously and compare results.

  How It Works

  ┌─────────────────────────────────────────────────────────────────┐
  │                     CLAIM SUBMISSION                             │
  │                          │                                       │
  │          ┌───────────────┴───────────────┐                      │
  │          ▼                               ▼                      │
  │   ┌──────────────┐               ┌──────────────┐               │
  │   │ CODE-DRIVEN  │               │ AGENT-DRIVEN │               │
  │   │ (Deterministic)              │ (AI/LLM)     │               │
  │   └──────┬───────┘               └──────┬───────┘               │
  │          │                               │                      │
  │          │ ~100-200ms                    │ ~2-5 seconds         │
  │          ▼                               ▼                      │
  │   ┌──────────────┐               ┌──────────────┐               │
  │   │ Decision:    │               │ Decision:    │               │
  │   │ APPROVE      │               │ MANUAL_REVIEW│               │
  │   │ Risk: LOW    │               │ Risk: MEDIUM │               │
  │   │ (no reasoning)│              │ + Reasoning  │               │
  │   └──────────────┘               │ + Insights   │               │
  │                                  └──────────────┘               │
  │                          │                                       │
  │                          ▼                                       │
  │                   ┌──────────────┐                              │
  │                   │  COMPARISON  │                              │
  │                   │  METRICS     │                              │
  │                   └──────────────┘                              │
  └─────────────────────────────────────────────────────────────────┘

  Backend Implementation

  # ws6_agent_pipeline/app/routers/comparison.py

  @router.post("/run")
  async def run_comparison(claim_data: dict):
      # Run BOTH in parallel (not sequential)
      code_task = asyncio.create_task(code_processor.process_claim(claim_data))
      agent_task = asyncio.create_task(medallion_pipeline.process_claim(claim_data))

      code_result, agent_result = await asyncio.gather(code_task, agent_task)

      return {
          "code_driven": {
              "decision": "APPROVE",
              "processing_time_ms": 145,
              "risk_level": "low",
              "payout": 450.00
              # NO reasoning - just rules
          },
          "agent_driven": {
              "decision": "MANUAL_REVIEW",
              "processing_time_ms": 3200,
              "risk_level": "medium",
              "reasoning": "Customer has 3 similar claims in 6 months...",
              "insights": ["Claim frequency above average", "Same diagnosis pattern"]
          }
      }

  Code-Driven vs Agent-Driven
  ┌─────────────────┬─────────────────────┬──────────────────────────┐
  │     Aspect      │     Code-Driven     │       Agent-Driven       │
  ├─────────────────┼─────────────────────┼──────────────────────────┤
  │ Speed           │ ~100-200ms          │ ~2-5 seconds             │
  ├─────────────────┼─────────────────────┼──────────────────────────┤
  │ Logic           │ Fixed IF/ELSE rules │ LLM reasoning with tools │
  ├─────────────────┼─────────────────────┼──────────────────────────┤
  │ Reasoning       │ None (black box)    │ Full explanation         │
  ├─────────────────┼─────────────────────┼──────────────────────────┤
  │ Fraud Detection │ Threshold-based     │ Pattern matching         │
  ├─────────────────┼─────────────────────┼──────────────────────────┤
  │ Cost            │ Free                │ ~$0.01-0.05/claim        │
  ├─────────────────┼─────────────────────┼──────────────────────────┤
  │ Edge Cases      │ May miss            │ Adapts to novel patterns │
  └─────────────────┴─────────────────────┴──────────────────────────┘
  Example: Where They Differ

  Claim: $450 routine checkup, but customer has submitted 3 similar claims in 6 months

  Code-Driven Result:
  {
    "decision": "APPROVE",
    "reason": "Amount < $500 threshold, valid policy"
  }
  Code sees: Low amount ✓, valid data ✓ → Auto-approve

  Agent-Driven Result:
  {
    "decision": "MANUAL_REVIEW",
    "reasoning": "While amount is low, I detected a velocity pattern: 3 similar claims in 6 months for the same body area. This warrants human review.",
    "fraud_indicators": ["velocity_check: HIGH"]
  }
  Agent sees: Pattern across time → Flag for review

  When to Use Each
  ┌─────────────────────────────┬───────────────────────────┐
  │          Use Case           │      Recommendation       │
  ├─────────────────────────────┼───────────────────────────┤
  │ High-volume wellness claims │ Code (speed, cost)        │
  ├─────────────────────────────┼───────────────────────────┤
  │ Complex/high-value claims   │ Agent (reasoning)         │
  ├─────────────────────────────┼───────────────────────────┤
  │ Fraud investigation         │ Agent (pattern detection) │
  ├─────────────────────────────┼───────────────────────────┤
  │ Audit trail needed          │ Agent (explainability)    │
  ├─────────────────────────────┼───────────────────────────┤
  │ Cost-sensitive operations   │ Code (no API costs)       │
  └─────────────────────────────┴───────────────────────────┘
  The comparison tab helps you decide which approach to use for different claim types in production.


  