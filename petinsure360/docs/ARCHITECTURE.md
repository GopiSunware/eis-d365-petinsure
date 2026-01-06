# PetInsure360 - Architecture Document

## Executive Summary

PetInsure360 is a complete enterprise data platform for pet insurance, demonstrating modern data engineering patterns on Azure. The platform implements a **medallion lakehouse architecture** with real-time data ingestion, batch ETL processing, and self-service BI capabilities.

### Live Deployment (2026-01-01)

| Component | URL | Status |
|-----------|-----|--------|
| Customer Portal | https://petinsure360frontend.z5.web.core.windows.net | **LIVE** |
| Backend API | https://petinsure360-backend.azurewebsites.net | **LIVE** |
| API Documentation | https://petinsure360-backend.azurewebsites.net/docs | **LIVE** |
| Databricks Workspace | https://adb-7405619408519767.7.azuredatabricks.net | **LIVE** |
| Synapse Studio | https://web.azuresynapse.net | **Ready** |

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Layers](#2-architecture-layers)
3. [Complete Data Flow](#3-complete-data-flow)
4. [Component Details](#4-component-details)
5. [Data Model](#5-data-model)
6. [Technology Stack](#6-technology-stack)
7. [Deployment Architecture](#7-deployment-architecture)
8. [Security Architecture](#8-security-architecture)
9. [API Specifications](#9-api-specifications)

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    PETINSURE360 ARCHITECTURE                                            │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                         │
│   ┌───────────────────────────────────────────────────────────────────────────────────────────────┐    │
│   │                              PRESENTATION LAYER                                                │    │
│   │  ┌─────────────────────┐              ┌─────────────────────┐                                  │    │
│   │  │   CUSTOMER PORTAL   │              │    BI DASHBOARD     │                                  │    │
│   │  │   (React SPA)       │              │    (React SPA)      │                                  │    │
│   │  │   Port: 3000        │              │    Port: 3001       │                                  │    │
│   │  │                     │              │                     │                                  │    │
│   │  │ • Customer Register │              │ • Executive KPIs    │                                  │    │
│   │  │ • Pet Management    │              │ • Customer 360      │                                  │    │
│   │  │ • Policy Purchase   │              │ • Claims Analytics  │                                  │    │
│   │  │ • Claim Submission  │              │ • Risk Analysis     │                                  │    │
│   │  │ • Real-time Status  │              │ • Cross-Sell Opps   │                                  │    │
│   │  └──────────┬──────────┘              └──────────┬──────────┘                                  │    │
│   └─────────────┼────────────────────────────────────┼──────────────────────────────────────────────┘    │
│                 │                                    │                                                   │
│                 │ HTTP/WebSocket                     │ HTTP                                              │
│                 ▼                                    ▼                                                   │
│   ┌───────────────────────────────────────────────────────────────────────────────────────────────┐    │
│   │                              API LAYER (FastAPI)                                               │    │
│   │  ┌─────────────────────────────────────────────────────────────────────────────────────────┐  │    │
│   │  │                           BACKEND API - Port 8000                                       │  │    │
│   │  │  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐                    │  │    │
│   │  │  │ Data Ingestion    │  │ BI Insights       │  │ WebSocket         │                    │  │    │
│   │  │  │ ─────────────     │  │ ──────────        │  │ ─────────         │                    │  │    │
│   │  │  │ POST /customers   │  │ GET /insights/kpis│  │ Socket.IO         │                    │  │    │
│   │  │  │ POST /pets        │  │ GET /insights/    │  │ Real-time events  │                    │  │    │
│   │  │  │ POST /policies    │  │     customers     │  │ • claim_submitted │                    │  │    │
│   │  │  │ POST /claims      │  │ GET /insights/    │  │ • status_update   │                    │  │    │
│   │  │  │                   │  │     claims        │  │ • notifications   │                    │  │    │
│   │  │  └─────────┬─────────┘  └─────────┬─────────┘  └───────────────────┘                    │  │    │
│   │  └────────────┼──────────────────────┼─────────────────────────────────────────────────────┘  │    │
│   └───────────────┼──────────────────────┼────────────────────────────────────────────────────────┘    │
│                   │                      │                                                             │
│                   │ Azure SDK            │ Read from                                                   │
│                   │ (Write JSON)         │ Gold Layer                                                  │
│                   ▼                      ▼                                                             │
│   ┌───────────────────────────────────────────────────────────────────────────────────────────────┐    │
│   │                              DATA PLATFORM LAYER (Azure)                                       │    │
│   │                                                                                                │    │
│   │  ┌──────────────────────────────────────────────────────────────────────────────────────────┐ │    │
│   │  │                    AZURE DATA LAKE STORAGE GEN2 (petinsud7i43)                           │ │    │
│   │  │  ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐                    │ │    │
│   │  │  │    raw/    │    │   bronze/  │    │   silver/  │    │    gold/   │                    │ │    │
│   │  │  │  ────────  │    │  ────────  │    │  ────────  │    │  ────────  │                    │ │    │
│   │  │  │ • JSON     │───▶│ • Delta    │───▶│ • Delta    │───▶│ • Delta    │                    │ │    │
│   │  │  │ • CSV      │    │   Tables   │    │   Tables   │    │   Tables   │                    │ │    │
│   │  │  │ • JSONL    │    │ • Raw      │    │ • Cleansed │    │ • Business │                    │ │    │
│   │  │  │            │    │ • Metadata │    │ • Quality  │    │   Views    │                    │ │    │
│   │  │  └────────────┘    └────────────┘    └────────────┘    └────────────┘                    │ │    │
│   │  └──────────────────────────────────────────────────────────────────────────────────────────┘ │    │
│   │                                          │                                                     │    │
│   │                                          │ ETL Pipeline                                        │    │
│   │                                          ▼                                                     │    │
│   │  ┌──────────────────────────────────────────────────────────────────────────────────────────┐ │    │
│   │  │                         AZURE DATABRICKS                                                 │ │    │
│   │  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                           │ │    │
│   │  │  │ 01_bronze       │  │ 02_silver       │  │ 03_gold         │                           │ │    │
│   │  │  │ _ingestion.py   │─▶│ _transform.py   │─▶│ _aggregations   │                           │ │    │
│   │  │  │                 │  │                 │  │ .py             │                           │ │    │
│   │  │  │ • Read raw data │  │ • Type casting  │  │ • Customer 360  │                           │ │    │
│   │  │  │ • Add metadata  │  │ • Deduplication │  │ • Claims Agg    │                           │ │    │
│   │  │  │ • Write Delta   │  │ • Quality score │  │ • Monthly KPIs  │                           │ │    │
│   │  │  └─────────────────┘  └─────────────────┘  │ • Risk Scoring  │                           │ │    │
│   │  │                                            │ • Cross-Sell    │                           │ │    │
│   │  │                                            └─────────────────┘                           │ │    │
│   │  └──────────────────────────────────────────────────────────────────────────────────────────┘ │    │
│   │                                                                                                │    │
│   │  ┌─────────────────────────┐  ┌─────────────────────────┐                                     │    │
│   │  │   AZURE SYNAPSE         │  │   AZURE KEY VAULT       │                                     │    │
│   │  │   (Serverless SQL)      │  │   (Secrets)             │                                     │    │
│   │  │   • Query Gold Layer    │  │   • Storage Keys        │                                     │    │
│   │  │   • Power BI Backend    │  │   • API Keys            │                                     │    │
│   │  └─────────────────────────┘  └─────────────────────────┘                                     │    │
│   └───────────────────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Key Principles

| Principle | Implementation |
|-----------|----------------|
| **Medallion Architecture** | Bronze → Silver → Gold layers for progressive data refinement |
| **Delta Lake** | ACID transactions, time travel, schema evolution |
| **Event-Driven** | WebSocket for real-time status updates |
| **API-First** | RESTful APIs for all data operations |
| **Separation of Concerns** | Distinct layers for ingestion, processing, and presentation |

---

## 2. Architecture Layers

### 2.1 Layer Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ARCHITECTURE LAYERS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Layer 1: PRESENTATION                                                       │
│  ─────────────────────                                                       │
│  │ Customer Portal │ ─── User interactions, forms, real-time updates        │
│  │ BI Dashboard    │ ─── Analytics, charts, reports                         │
│                                                                              │
│  Layer 2: API / SERVICE                                                      │
│  ─────────────────────                                                       │
│  │ FastAPI Backend │ ─── REST endpoints, WebSocket, business logic          │
│  │ Storage Service │ ─── Azure SDK integration for ADLS writes              │
│  │ Insights Service│ ─── Query Gold layer, compute analytics                │
│                                                                              │
│  Layer 3: DATA INGESTION                                                     │
│  ───────────────────────                                                     │
│  │ Raw Container   │ ─── JSON/CSV files from API and batch uploads          │
│                                                                              │
│  Layer 4: DATA PROCESSING                                                    │
│  ────────────────────────                                                    │
│  │ Bronze Layer    │ ─── Raw data with metadata                             │
│  │ Silver Layer    │ ─── Cleansed, validated, quality-scored                │
│  │ Gold Layer      │ ─── Business aggregations, analytics-ready             │
│                                                                              │
│  Layer 5: DATA SERVING                                                       │
│  ─────────────────────                                                       │
│  │ Synapse SQL     │ ─── Serverless queries for BI tools                    │
│  │ Delta Tables    │ ─── Direct queries from API                            │
│                                                                              │
│  Layer 6: INFRASTRUCTURE                                                     │
│  ──────────────────────                                                      │
│  │ Terraform IaC   │ ─── Azure resource provisioning                        │
│  │ Key Vault       │ ─── Secrets management                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Complete Data Flow

### 3.1 End-to-End Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    COMPLETE DATA FLOW                                                   │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                         │
│  STEP 1: USER INTERACTION                                                                               │
│  ════════════════════════                                                                               │
│                                                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                              CUSTOMER PORTAL (React)                                             │   │
│  │                                                                                                  │   │
│  │    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │   │
│  │    │   REGISTER   │    │   ADD PET    │    │ BUY POLICY   │    │SUBMIT CLAIM  │                  │   │
│  │    │   CUSTOMER   │    │              │    │              │    │              │                  │   │
│  │    │              │    │ Name, Breed  │    │ Select Plan  │    │ Service Date │                  │   │
│  │    │ Name, Email  │    │ DOB, Weight  │    │ Add-ons      │    │ Amount       │                  │   │
│  │    │ Address      │    │ Vaccination  │    │ Payment      │    │ Diagnosis    │                  │   │
│  │    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │   │
│  │           │                   │                   │                   │                          │   │
│  │           └───────────────────┴───────────────────┴───────────────────┘                          │   │
│  │                                           │                                                      │   │
│  └───────────────────────────────────────────┼──────────────────────────────────────────────────────┘   │
│                                              │                                                          │
│                                              │ HTTP POST (JSON)                                         │
│                                              ▼                                                          │
│  STEP 2: API PROCESSING                                                                                 │
│  ══════════════════════                                                                                 │
│                                                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                              FASTAPI BACKEND                                                     │   │
│  │                                                                                                  │   │
│  │    ┌─────────────────────────────────────────────────────────────────────────────────────────┐  │   │
│  │    │                          REQUEST PROCESSING                                              │  │   │
│  │    │                                                                                          │  │   │
│  │    │    1. Receive HTTP Request                                                               │  │   │
│  │    │           │                                                                              │  │   │
│  │    │           ▼                                                                              │  │   │
│  │    │    2. Validate with Pydantic Schema                                                      │  │   │
│  │    │           │                                                                              │  │   │
│  │    │           ▼                                                                              │  │   │
│  │    │    3. Generate UUID (CUST-XXXX, PET-XXXX, POL-XXXX, CLM-XXXX)                            │  │   │
│  │    │           │                                                                              │  │   │
│  │    │           ▼                                                                              │  │   │
│  │    │    4. Add Metadata (timestamp, source)                                                   │  │   │
│  │    │           │                                                                              │  │   │
│  │    │           ├──────────────────────────────────────┐                                       │  │   │
│  │    │           │                                      │                                       │  │   │
│  │    │           ▼                                      ▼                                       │  │   │
│  │    │    5. Write to ADLS                       6. Emit WebSocket Event                        │  │   │
│  │    │       (Azure SDK)                            (Socket.IO)                                 │  │   │
│  │    │           │                                      │                                       │  │   │
│  │    │           ▼                                      ▼                                       │  │   │
│  │    │    7. Return Response                     8. Real-time Update                            │  │   │
│  │    │       with ID                                to Client                                   │  │   │
│  │    │                                                                                          │  │   │
│  │    └─────────────────────────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                                                  │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                              │                                                          │
│                                              │ Azure Blob SDK                                           │
│                                              ▼                                                          │
│  STEP 3: DATA STORAGE                                                                                   │
│  ════════════════════                                                                                   │
│                                                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                         AZURE DATA LAKE STORAGE GEN2                                             │   │
│  │                              (petinsud7i43)                                                      │   │
│  │                                                                                                  │   │
│  │    Container: raw/                                                                               │   │
│  │    ┌─────────────────────────────────────────────────────────────────────────────────────────┐  │   │
│  │    │                                                                                          │  │   │
│  │    │    customers/                                                                            │  │   │
│  │    │    ├── customers.csv           (batch - synthetic data)                                  │  │   │
│  │    │    └── CUST-ABC123_20241223_103045_123456.json  (real-time from API)                     │  │   │
│  │    │                                                                                          │  │   │
│  │    │    pets/                                                                                 │  │   │
│  │    │    ├── pets.csv                                                                          │  │   │
│  │    │    └── PET-DEF456_20241223_103050_789012.json                                            │  │   │
│  │    │                                                                                          │  │   │
│  │    │    policies/                                                                             │  │   │
│  │    │    ├── policies.csv                                                                      │  │   │
│  │    │    └── POL-GHI789_20241223_103055_345678.json                                            │  │   │
│  │    │                                                                                          │  │   │
│  │    │    claims/                                                                               │  │   │
│  │    │    ├── claims.jsonl            (batch - synthetic data)                                  │  │   │
│  │    │    └── CLM-JKL012_20241223_103100_901234.json  (real-time from API)                      │  │   │
│  │    │                                                                                          │  │   │
│  │    └─────────────────────────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                                                  │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                              │                                                          │
│                                              │ Databricks Job (Scheduled/Manual)                        │
│                                              ▼                                                          │
│  STEP 4: ETL PROCESSING                                                                                 │
│  ══════════════════════                                                                                 │
│                                                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                              AZURE DATABRICKS ETL PIPELINE                                       │   │
│  │                                                                                                  │   │
│  │    ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐                │   │
│  │    │                     │    │                     │    │                     │                │   │
│  │    │  01_BRONZE          │    │  02_SILVER          │    │  03_GOLD            │                │   │
│  │    │  INGESTION          │───▶│  TRANSFORMATIONS    │───▶│  AGGREGATIONS       │                │   │
│  │    │                     │    │                     │    │                     │                │   │
│  │    │  ┌───────────────┐  │    │  ┌───────────────┐  │    │  ┌───────────────┐  │                │   │
│  │    │  │ Read CSV/JSON │  │    │  │ Type Casting  │  │    │  │customer_360   │  │                │   │
│  │    │  │ from raw/     │  │    │  │ • Dates       │  │    │  │ _view         │  │                │   │
│  │    │  └───────┬───────┘  │    │  │ • Numbers     │  │    │  │               │  │                │   │
│  │    │          │          │    │  │ • Strings     │  │    │  │ - Customer    │  │                │   │
│  │    │  ┌───────▼───────┐  │    │  └───────┬───────┘  │    │  │   profile     │  │                │   │
│  │    │  │ Add Metadata  │  │    │          │          │    │  │ - Pet summary │  │                │   │
│  │    │  │ • Timestamp   │  │    │  ┌───────▼───────┐  │    │  │ - Policies    │  │                │   │
│  │    │  │ • Source file │  │    │  │Deduplication  │  │    │  │ - Claims      │  │                │   │
│  │    │  │ • Batch ID    │  │    │  │ (keep latest) │  │    │  │ - Risk score  │  │                │   │
│  │    │  └───────┬───────┘  │    │  └───────┬───────┘  │    │  │ - Value tier  │  │                │   │
│  │    │          │          │    │          │          │    │  └───────────────┘  │                │   │
│  │    │  ┌───────▼───────┐  │    │  ┌───────▼───────┐  │    │                     │                │   │
│  │    │  │ Write to      │  │    │  │Quality Score  │  │    │  ┌───────────────┐  │                │   │
│  │    │  │ Bronze Delta  │  │    │  │ (0-100)       │  │    │  │claims_        │  │                │   │
│  │    │  │ Tables        │  │    │  └───────┬───────┘  │    │  │ analytics     │  │                │   │
│  │    │  └───────────────┘  │    │          │          │    │  │               │  │                │   │
│  │    │                     │    │  ┌───────▼───────┐  │    │  │ - All dims    │  │                │   │
│  │    │  Tables:            │    │  │Standardize    │  │    │  │ - Categories  │  │                │   │
│  │    │  • customers_raw    │    │  │ • Phone       │  │    │  │ - Status      │  │                │   │
│  │    │  • pets_raw         │    │  │ • Email       │  │    │  │ - Amounts     │  │                │   │
│  │    │  • policies_raw     │    │  │ • State       │  │    │  └───────────────┘  │                │   │
│  │    │  • claims_raw       │    │  └───────┬───────┘  │    │                     │                │   │
│  │    │  • providers_raw    │    │          │          │    │  ┌───────────────┐  │                │   │
│  │    │                     │    │  ┌───────▼───────┐  │    │  │monthly_kpis   │  │                │   │
│  │    │                     │    │  │ Write to      │  │    │  │               │  │                │   │
│  │    │                     │    │  │ Silver Delta  │  │    │  │ - Claims cnt  │  │                │   │
│  │    │                     │    │  │ Tables        │  │    │  │ - Premium     │  │                │   │
│  │    │                     │    │  └───────────────┘  │    │  │ - Loss ratio  │  │                │   │
│  │    │                     │    │                     │    │  │ - Growth %    │  │                │   │
│  │    │                     │    │  Tables:            │    │  └───────────────┘  │                │   │
│  │    │                     │    │  • dim_customers    │    │                     │                │   │
│  │    │                     │    │  • dim_pets         │    │  ┌───────────────┐  │                │   │
│  │    │                     │    │  • dim_policies     │    │  │cross_sell_    │  │                │   │
│  │    │                     │    │  • dim_providers    │    │  │recommendations│  │                │   │
│  │    │                     │    │  • fact_claims      │    │  │               │  │                │   │
│  │    │                     │    │                     │    │  │ - Opportunity │  │                │   │
│  │    │                     │    │                     │    │  │ - Revenue     │  │                │   │
│  │    │                     │    │                     │    │  └───────────────┘  │                │   │
│  │    │                     │    │                     │    │                     │                │   │
│  │    └─────────────────────┘    └─────────────────────┘    │  ┌───────────────┐  │                │   │
│  │                                                          │  │risk_scoring   │  │                │   │
│  │                                                          │  │               │  │                │   │
│  │                                                          │  │ - Risk score  │  │                │   │
│  │                                                          │  │ - Category    │  │                │   │
│  │                                                          │  │ - Actions     │  │                │   │
│  │                                                          │  └───────────────┘  │                │   │
│  │                                                          │                     │                │   │
│  │                                                          └─────────────────────┘                │   │
│  │                                                                                                  │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                              │                                                          │
│                                              │ Query Gold Layer                                         │
│                                              ▼                                                          │
│  STEP 5: DATA SERVING                                                                                   │
│  ════════════════════                                                                                   │
│                                                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                              INSIGHTS SERVICE                                                    │   │
│  │                                                                                                  │   │
│  │    ┌─────────────────────────────────────────────────────────────────────────────────────────┐  │   │
│  │    │                          GOLD LAYER QUERIES                                              │  │   │
│  │    │                                                                                          │  │   │
│  │    │    GET /api/insights/kpis ──────────▶ monthly_kpis table                                 │  │   │
│  │    │    GET /api/insights/customers ─────▶ customer_360_view table                            │  │   │
│  │    │    GET /api/insights/claims ────────▶ claims_analytics table                             │  │   │
│  │    │    GET /api/insights/risks ─────────▶ risk_scoring table                                 │  │   │
│  │    │    GET /api/insights/cross-sell ────▶ cross_sell_recommendations table                   │  │   │
│  │    │    GET /api/insights/providers ─────▶ provider_performance table                         │  │   │
│  │    │                                                                                          │  │   │
│  │    └─────────────────────────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                                                  │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                              │                                                          │
│                                              │ JSON Response                                            │
│                                              ▼                                                          │
│  STEP 6: BI VISUALIZATION                                                                               │
│  ════════════════════════                                                                               │
│                                                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                              BI DASHBOARD (React)                                                │   │
│  │                                                                                                  │   │
│  │    ┌─────────────────────────────────────────────────────────────────────────────────────────┐  │   │
│  │    │                                                                                          │  │   │
│  │    │    ┌───────────────────────────────────────────────────────────────────────────────┐    │  │   │
│  │    │    │                         EXECUTIVE DASHBOARD                                    │    │  │   │
│  │    │    │    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐                   │    │  │   │
│  │    │    │    │ 15,000  │    │  78%    │    │  68%    │    │ 4.2 d   │                   │    │  │   │
│  │    │    │    │ Claims  │    │Approval │    │LossRatio│    │Avg Proc │                   │    │  │   │
│  │    │    │    └─────────┘    └─────────┘    └─────────┘    └─────────┘                   │    │  │   │
│  │    │    │                                                                                │    │  │   │
│  │    │    │    ┌────────────────────────────┐  ┌────────────────────────────┐              │    │  │   │
│  │    │    │    │    CLAIMS TREND CHART      │  │   CUSTOMER SEGMENTS PIE    │              │    │  │   │
│  │    │    │    │         (Recharts)         │  │         (Recharts)         │              │    │  │   │
│  │    │    │    └────────────────────────────┘  └────────────────────────────┘              │    │  │   │
│  │    │    └───────────────────────────────────────────────────────────────────────────────┘    │  │   │
│  │    │                                                                                          │  │   │
│  │    │    ┌───────────────────────────────────────────────────────────────────────────────┐    │  │   │
│  │    │    │                         CUSTOMER 360 VIEW                                      │    │  │   │
│  │    │    │    ┌─────────────────────────────────────────────────────────────────────┐    │    │  │   │
│  │    │    │    │ John Smith | Platinum | Low Risk | LTV: $1,440 | Claims: 3          │    │    │  │   │
│  │    │    │    │ Pets: 2 | Active Policies: 2 | Loss Ratio: 45%                      │    │    │  │   │
│  │    │    │    │ Cross-sell: Multi-Pet Discount ($300/yr opportunity)                │    │    │  │   │
│  │    │    │    └─────────────────────────────────────────────────────────────────────┘    │    │  │   │
│  │    │    └───────────────────────────────────────────────────────────────────────────────┘    │  │   │
│  │    │                                                                                          │  │   │
│  │    └─────────────────────────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                                                  │   │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Sequence Diagram - Claim Submission Flow

```
┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐
│   User     │   │  Frontend  │   │   Backend  │   │    ADLS    │   │ Databricks │   │BI Dashboard│
│            │   │   (React)  │   │  (FastAPI) │   │  (Storage) │   │   (ETL)    │   │  (React)   │
└─────┬──────┘   └─────┬──────┘   └─────┬──────┘   └─────┬──────┘   └─────┬──────┘   └─────┬──────┘
      │                │                │                │                │                │
      │ 1. Fill Claim  │                │                │                │                │
      │    Form        │                │                │                │                │
      ├───────────────▶│                │                │                │                │
      │                │                │                │                │                │
      │                │ 2. POST        │                │                │                │
      │                │  /api/claims   │                │                │                │
      │                ├───────────────▶│                │                │                │
      │                │                │                │                │                │
      │                │                │ 3. Validate    │                │                │
      │                │                │    & Generate  │                │                │
      │                │                │    Claim ID    │                │                │
      │                │                │                │                │                │
      │                │                │ 4. Write JSON  │                │                │
      │                │                ├───────────────▶│                │                │
      │                │                │                │                │                │
      │                │                │ 5. WebSocket   │                │                │
      │                │                │    Event       │                │                │
      │                │◀───────────────┤                │                │                │
      │                │"claim_submitted"                │                │                │
      │                │                │                │                │                │
      │ 6. Toast       │                │                │                │                │
      │   Notification │                │                │                │                │
      │◀───────────────┤                │                │                │                │
      │                │                │                │                │                │
      │                │ 7. Response    │                │                │                │
      │                │◀───────────────┤                │                │                │
      │                │  {claim_id,    │                │                │                │
      │                │   claim_number}│                │                │                │
      │                │                │                │                │                │
      │ 8. Show        │                │                │                │                │
      │   Confirmation │                │                │                │                │
      │◀───────────────┤                │                │                │                │
      │                │                │                │                │                │
      │                │                │                │ 9. ETL Job     │                │
      │                │                │                │    Triggered   │                │
      │                │                │                ├───────────────▶│                │
      │                │                │                │                │                │
      │                │                │                │                │ 10. Bronze     │
      │                │                │                │                │     Silver     │
      │                │                │                │                │     Gold       │
      │                │                │                │                │                │
      │                │                │                │                │ 11. Update     │
      │                │                │                │                │     Gold Tables│
      │                │                │                │                │                │
      │                │                │                │                │                │
      │                │                │                │ 12. Query Gold │                │
      │                │                │                │◀───────────────┼────────────────│
      │                │                │                │                │                │
      │                │                │                │                │ 13. New claim  │
      │                │                │                │                │     visible    │
      │                │                │                │                ├───────────────▶│
      │                │                │                │                │                │
```

---

## 4. Component Details

### 4.1 Customer Portal (Frontend)

| Component | Description |
|-----------|-------------|
| **Framework** | React 18 + Vite |
| **Styling** | TailwindCSS |
| **Real-time** | Socket.io-client |
| **HTTP** | Axios |
| **Port** | 3000 |

**Pages:**
- `HomePage` - Landing page with features overview
- `RegisterPage` - Customer registration form
- `AddPetPage` - Pet profile creation
- `PolicyPage` - Insurance plan selection and purchase
- `ClaimPage` - Claim submission with real-time status

### 4.2 Backend API

| Component | Description |
|-----------|-------------|
| **Framework** | FastAPI |
| **WebSocket** | Python-SocketIO |
| **Storage** | Azure Storage SDK |
| **Validation** | Pydantic |
| **Port** | 8000 |

**Services:**
- `StorageService` - Writes JSON to ADLS Gen2
- `InsightsService` - Queries Gold layer data

### 4.3 Databricks ETL

| Notebook | Purpose |
|----------|---------|
| `01_bronze_ingestion.py` | Ingest raw data, add metadata |
| `02_silver_transformations.py` | Cleanse, dedupe, quality score |
| `03_gold_aggregations.py` | Business aggregations |
| `04_verify_data.py` | Data verification queries |

### 4.4 BI Dashboard

| Component | Description |
|-----------|-------------|
| **Framework** | React 18 + Vite |
| **Charts** | Recharts |
| **Styling** | TailwindCSS |
| **Real-time** | Socket.io-client for WebSocket updates |
| **Port** | 3001 |

**Pages:**
- `DashboardPage` - Executive KPIs and trends
- `CustomersPage` - Customer 360 view with search and filtering
- `ClaimsPage` - Claims analytics with drill-down
- `RisksPage` - Risk analysis and cross-sell recommendations
- `PipelinePage` - **NEW** Visual Medallion architecture (Bronze→Silver→Gold) with record counts

**Real-time Features:**
- WebSocket connection indicator in header
- Auto-refresh when new data is submitted via Customer Portal
- Toast notifications for new claims/customers

---

## 5. Data Model

### 5.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    DATA MODEL                                            │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐                │
│  │    CUSTOMERS    │       │      PETS       │       │    POLICIES     │                │
│  ├─────────────────┤       ├─────────────────┤       ├─────────────────┤                │
│  │ customer_id PK  │──┐    │ pet_id PK       │──┐    │ policy_id PK    │                │
│  │ first_name      │  │    │ customer_id FK  │◀─┘    │ policy_number   │                │
│  │ last_name       │  │    │ pet_name        │  │    │ customer_id FK  │◀───────────┐   │
│  │ email           │  │    │ species         │  └───▶│ pet_id FK       │            │   │
│  │ phone           │  │    │ breed           │       │ plan_name       │            │   │
│  │ address         │  │    │ gender          │       │ monthly_premium │            │   │
│  │ city            │  └───▶│ date_of_birth   │       │ deductible      │            │   │
│  │ state           │       │ weight_lbs      │       │ coverage_limit  │            │   │
│  │ zip_code        │       │ microchip_id    │       │ effective_date  │            │   │
│  │ date_of_birth   │       │ is_neutered     │       │ expiration_date │            │   │
│  │ customer_since  │       │ vaccination     │       │ status          │            │   │
│  │ segment         │       │ pre_existing    │       │ includes_*      │            │   │
│  │ lifetime_value  │       │ is_active       │       │                 │            │   │
│  └─────────────────┘       └─────────────────┘       └────────┬────────┘            │   │
│          │                                                    │                      │   │
│          │                                                    │                      │   │
│          │                 ┌─────────────────┐                │                      │   │
│          │                 │     CLAIMS      │                │                      │   │
│          │                 ├─────────────────┤                │                      │   │
│          │                 │ claim_id PK     │                │                      │   │
│          │                 │ claim_number    │                │                      │   │
│          └────────────────▶│ customer_id FK  │◀───────────────┘                      │   │
│                            │ policy_id FK    │                                       │   │
│                            │ pet_id FK       │                                       │   │
│                            │ provider_id FK  │◀──────────────────────────────────────│───┤
│                            │ claim_type      │                                       │   │
│                            │ claim_category  │       ┌─────────────────┐             │   │
│                            │ service_date    │       │  VET_PROVIDERS  │             │   │
│                            │ claim_amount    │       ├─────────────────┤             │   │
│                            │ paid_amount     │       │ provider_id PK  │─────────────┘   │
│                            │ status          │       │ provider_name   │                 │
│                            │ processing_days │       │ provider_type   │                 │
│                            │ denial_reason   │       │ address         │                 │
│                            └─────────────────┘       │ is_in_network   │                 │
│                                                      │ average_rating  │                 │
│                                                      │ specialties     │                 │
│                                                      └─────────────────┘                 │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Gold Layer Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `customer_360_view` | Unified customer profile | customer_id, total_pets, total_policies, loss_ratio, value_tier, risk_score |
| `claims_analytics` | Claims with all dimensions | claim_id, customer_name, pet_name, provider_name, amounts, status |
| `monthly_kpis` | Executive metrics | year_month, total_claims, approval_rate, loss_ratio, growth_pct |
| `cross_sell_recommendations` | Upsell opportunities | customer_id, recommendation, estimated_revenue |
| `provider_performance` | Vet network analytics | provider_id, total_claims, avg_claim_amount, rating |
| `risk_scoring` | Customer risk assessment | customer_id, total_risk_score, risk_category |

---

## 6. Technology Stack

### 6.1 Complete Stack

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TECHNOLOGY STACK                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FRONTEND                                                                    │
│  ────────                                                                    │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐                │
│  │   React    │ │   Vite     │ │ TailwindCSS│ │  Recharts  │                │
│  │    18.2    │ │    5.0     │ │    3.4     │ │    2.10    │                │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘                │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                               │
│  │Socket.io   │ │   Axios    │ │Lucide React│                               │
│  │  Client    │ │    1.6     │ │   0.303    │                               │
│  └────────────┘ └────────────┘ └────────────┘                               │
│                                                                              │
│  BACKEND                                                                     │
│  ───────                                                                     │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐                │
│  │  FastAPI   │ │  Uvicorn   │ │SocketIO    │ │  Pydantic  │                │
│  │   0.109    │ │   0.27     │ │    5.10    │ │    2.5     │                │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘                │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                               │
│  │Azure Blob  │ │  Pandas    │ │Python-dotenv                               │
│  │  SDK 12    │ │    2.1     │ │    1.0     │                               │
│  └────────────┘ └────────────┘ └────────────┘                               │
│                                                                              │
│  DATA PLATFORM                                                               │
│  ─────────────                                                               │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐                │
│  │ Databricks │ │ Delta Lake │ │   Spark    │ │   Synapse  │                │
│  │            │ │            │ │   3.5+     │ │ Serverless │                │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘                │
│                                                                              │
│  INFRASTRUCTURE                                                              │
│  ──────────────                                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐                │
│  │ Terraform  │ │ ADLS Gen2  │ │  Key Vault │ │   Azure    │                │
│  │    1.0+    │ │            │ │            │ │    CLI     │                │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Deployment Architecture

### 7.1 Azure Resources

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     AZURE DEPLOYMENT (West US 2)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Resource Group: rg-petinsure360                                             │
│  ──────────────────────────────                                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │ STORAGE ACCOUNT: petinsud7i43                                 │   │    │
│  │  │ Type: StorageV2 with Hierarchical Namespace (ADLS Gen2)       │   │    │
│  │  │                                                               │   │    │
│  │  │  Containers:                                                  │   │    │
│  │  │  ├── raw/     ─── Raw JSON/CSV from API and batch            │   │    │
│  │  │  ├── bronze/  ─── Bronze Delta tables                        │   │    │
│  │  │  ├── silver/  ─── Silver Delta tables                        │   │    │
│  │  │  ├── gold/    ─── Gold Delta tables                          │   │    │
│  │  │  └── synapse/ ─── Synapse workspace storage                  │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │ DATABRICKS WORKSPACE: petinsure360-databricks-dev             │   │    │
│  │  │ URL: adb-7405619408519767.7.azuredatabricks.net              │   │    │
│  │  │ SKU: Standard                                                 │   │    │
│  │  │                                                               │   │    │
│  │  │  Notebooks:                                                   │   │    │
│  │  │  ├── 01_bronze_ingestion.py                                   │   │    │
│  │  │  ├── 02_silver_transformations.py                             │   │    │
│  │  │  ├── 03_gold_aggregations.py                                  │   │    │
│  │  │  └── 04_verify_data.py                                        │   │    │
│  │  │                                                               │   │    │
│  │  │  Job: petinsure360-etl-pipeline (ID: 591500457291311)         │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │ SYNAPSE WORKSPACE: petins-syn-ud7i43                          │   │    │
│  │  │ SQL Endpoint: petins-syn-ud7i43-ondemand.sql.azuresynapse.net│   │    │
│  │  │ Purpose: Serverless SQL for BI queries                       │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │ KEY VAULT: petins-kv-ud7i43                                   │   │    │
│  │  │ Secrets: storage-account-key                                  │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │ DATA FACTORY: petinsure360-adf-dev                            │   │    │
│  │  │ Purpose: Orchestration (optional, can use Databricks Jobs)   │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Production Deployment (Azure)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     AZURE PRODUCTION DEPLOYMENT                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FRONTEND HOSTING (Azure Blob Storage Static Websites)                       │
│  ─────────────────────────────────────────────────────                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Storage Account: petinsure360                                        │    │
│  │ Container: $web                                                      │    │
│  │ URL: https://petinsure360.z5.web.core.windows.net                   │    │
│  │ SPA Routing: 404 document → index.html                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Storage Account: petinsure360bi                                      │    │
│  │ Container: $web                                                      │    │
│  │ URL: https://petinsure360bi.z5.web.core.windows.net                 │    │
│  │ SPA Routing: 404 document → index.html                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  BACKEND HOSTING (Azure Web App)                                             │
│  ───────────────────────────────                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ App Service: petinsure360-backend                                    │    │
│  │ Plan: petinsure360-plan (B1 Basic)                                  │    │
│  │ Region: UK West                                                      │    │
│  │ Runtime: Python 3.11                                                │    │
│  │ URL: https://petinsure360-backend.azurewebsites.net                 │    │
│  │ Startup: gunicorn -k uvicorn.workers.UvicornWorker app.main:socket_app│   │
│  │                                                                      │    │
│  │ Environment Variables:                                               │    │
│  │ • AZURE_STORAGE_ACCOUNT=petinsud7i43                                │    │
│  │ • USE_LOCAL_DATA=true (uses bundled demo data)                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Local Development

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     LOCAL DEVELOPMENT SETUP                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Terminal 1: Backend API                                                     │
│  ───────────────────────                                                     │
│  cd petinsure360/backend                                                     │
│  pip install -r requirements.txt                                             │
│  python -m uvicorn app.main:socket_app --reload --port 8000                  │
│                                                                              │
│  Terminal 2: Customer Portal                                                 │
│  ───────────────────────────                                                 │
│  cd petinsure360/frontend                                                    │
│  npm install                                                                 │
│  npm run dev                         # http://localhost:3000                 │
│                                                                              │
│  Terminal 3: BI Dashboard                                                    │
│  ────────────────────────                                                    │
│  cd petinsure360/bi-dashboard                                                │
│  npm install                                                                 │
│  npm run dev                         # http://localhost:3001                 │
│                                                                              │
│  URLs:                                                                       │
│  ─────                                                                       │
│  • Backend API:     http://localhost:8000                                    │
│  • API Docs:        http://localhost:8000/docs                               │
│  • Customer Portal: http://localhost:3000                                    │
│  • BI Dashboard:    http://localhost:3001                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Security Architecture

### 8.1 Security Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SECURITY ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  AUTHENTICATION & AUTHORIZATION                                              │
│  ──────────────────────────────                                              │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ • Azure AD for Databricks workspace access                         │     │
│  │ • SAS tokens for storage access (demo)                             │     │
│  │ • Managed Identity (recommended for production)                    │     │
│  │ • API authentication via Bearer tokens (future enhancement)        │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  SECRETS MANAGEMENT                                                          │
│  ──────────────────                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ • Azure Key Vault stores storage account keys                      │     │
│  │ • Environment variables for local development                      │     │
│  │ • Databricks Secret Scopes (recommended for production)            │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  NETWORK SECURITY                                                            │
│  ────────────────                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ • Private endpoints (recommended for production)                   │     │
│  │ • Synapse firewall rules                                           │     │
│  │ • Storage firewall (can be configured)                             │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  DATA SECURITY                                                               │
│  ─────────────                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ • Encryption at rest (Azure Storage default)                       │     │
│  │ • Encryption in transit (HTTPS)                                    │     │
│  │ • Column-level encryption (future enhancement)                     │     │
│  │ • PII masking in Silver layer (future enhancement)                 │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. API Specifications

### 9.1 Data Ingestion Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/customers/` | POST | Register new customer |
| `/api/pets/` | POST | Add pet to customer |
| `/api/policies/` | POST | Create insurance policy |
| `/api/policies/plans/available` | GET | List available plans |
| `/api/claims/` | POST | Submit claim |
| `/api/claims/{id}/status` | GET | Get claim status |
| `/api/claims/{id}/simulate-processing` | POST | Demo: simulate claim processing |

### 9.2 BI Insights Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/insights/summary` | GET | Data summary stats |
| `/api/insights/kpis` | GET | Monthly KPI metrics |
| `/api/insights/customers` | GET | Customer 360 list |
| `/api/insights/customers/{id}` | GET | Single customer 360 |
| `/api/insights/claims` | GET | Claims analytics |
| `/api/insights/providers` | GET | Provider performance |
| `/api/insights/risks` | GET | Risk scores |
| `/api/insights/cross-sell` | GET | Cross-sell recommendations |
| `/api/insights/segments` | GET | Customer segments |

### 9.3 Pipeline Status Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/pipeline/status` | GET | Medallion layer statistics (Bronze/Silver/Gold) |
| `/health` | GET | Backend health check |

### 9.4 WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `connect` | Server→Client | Connection established |
| `customer_created` | Server→Client | New customer registered |
| `pet_added` | Server→Client | Pet added to customer |
| `policy_created` | Server→Client | Policy purchased |
| `claim_submitted` | Server→Client | Claim submitted |
| `claim_status_update` | Server→Client | Claim status changed |
| `subscribe_claims` | Client→Server | Subscribe to customer's claim updates |

---

## Author

**Gopinath Varadharajan**
- Email: gopi@sunwaretechnologies.com
- LinkedIn: [linkedin.com/in/vg1111](https://linkedin.com/in/vg1111)

---

*Document Version: 1.2*
*Last Updated: January 2026*
*Deployment Status: LIVE on Azure - ETL Pipeline Active*
