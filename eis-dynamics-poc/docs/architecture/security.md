# Security Architecture

## Overview

This document outlines the security architecture for the EIS-Dynamics POC, covering authentication, authorization, data protection, and infrastructure security across both AWS and Azure deployments.

## Security Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              SECURITY LAYERS                                             │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────────────────────────────────────┐
  │  EDGE SECURITY                                                                         │
  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                        │
  │  │   Azure WAF     │  │   DDoS Protect  │  │   TLS 1.3       │                        │
  │  │   (OWASP Rules) │  │   (Standard)    │  │   (Encryption)  │                        │
  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                        │
  └───────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
  ┌───────────────────────────────────────────────────────────────────────────────────────┐
  │  API GATEWAY SECURITY                                                                  │
  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                        │
  │  │  OAuth 2.0 /    │  │   Rate          │  │   Request       │                        │
  │  │  Azure AD       │  │   Limiting      │  │   Validation    │                        │
  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                        │
  │                                                                                        │
  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                        │
  │  │  API Key        │  │   IP            │  │   JWT           │                        │
  │  │  Management     │  │   Filtering     │  │   Validation    │                        │
  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                        │
  └───────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
  ┌───────────────────────────────────────────────────────────────────────────────────────┐
  │  APPLICATION SECURITY                                                                  │
  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                        │
  │  │  Input          │  │   RBAC          │  │   Audit         │                        │
  │  │  Validation     │  │   (Roles)       │  │   Logging       │                        │
  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                        │
  │                                                                                        │
  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                        │
  │  │  Managed        │  │   Secret        │  │   Secure        │                        │
  │  │  Identity       │  │   Injection     │  │   Coding        │                        │
  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                        │
  └───────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
  ┌───────────────────────────────────────────────────────────────────────────────────────┐
  │  DATA SECURITY                                                                         │
  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                        │
  │  │  Encryption     │  │   Key           │  │   Data          │                        │
  │  │  at Rest        │  │   Management    │  │   Masking       │                        │
  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                        │
  │                                                                                        │
  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                        │
  │  │  Encryption     │  │   Access        │  │   Backup        │                        │
  │  │  in Transit     │  │   Controls      │  │   Encryption    │                        │
  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                        │
  └───────────────────────────────────────────────────────────────────────────────────────┘
```

## Authentication

### WS8 Admin Portal Authentication (JWT)

The Admin Portal (WS8) implements JWT-based authentication for secure access to configuration and monitoring features.

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              WS8 JWT AUTHENTICATION FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  Admin Portal (8081)      WS8 Backend (8008)                      Protected Resources
       │                         │                                        │
       │  1. POST /api/v1/auth/login                                      │
       │     {username, password}│                                        │
       │ ───────────────────────▶│                                        │
       │                         │                                        │
       │                         │  2. Validate credentials               │
       │                         │     Check against user store           │
       │                         │─────────┐                              │
       │                         │         │                              │
       │                         │◀────────┘                              │
       │                         │                                        │
       │  3. JWT Token (HS256)   │                                        │
       │     {                   │                                        │
       │       sub: user_id,     │                                        │
       │       role: "admin",    │                                        │
       │       exp: 24h          │                                        │
       │     }                   │                                        │
       │ ◀───────────────────────│                                        │
       │                         │                                        │
       │  4. API Request         │                                        │
       │     Authorization:      │                                        │
       │     Bearer <token>      │                                        │
       │ ───────────────────────▶│                                        │
       │                         │                                        │
       │                         │  5. Verify JWT signature (HS256)       │
       │                         │     Check expiration                   │
       │                         │     Extract role                       │
       │                         │─────────┐                              │
       │                         │         │                              │
       │                         │◀────────┘                              │
       │                         │                                        │
       │                         │  6. Access config/cost/audit           │
       │                         │ ───────────────────────────────────────▶│
       │                         │                                        │
       │  7. Response            │                                        │
       │ ◀───────────────────────│                                        │
       │                         │                                        │
       ▼                         ▼                                        ▼

  JWT Configuration:
  • Algorithm: HS256
  • Expiration: 24 hours
  • Secret: Stored in environment variable or Azure Key Vault
```

### Azure AD Authentication Flow (Optional)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              OAUTH 2.0 FLOW (AZURE AD SSO)                               │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  Agent Portal           Azure AD                 API Gateway              Backend API
       │                    │                          │                       │
       │  1. Login Request  │                          │                       │
       │ ──────────────────▶│                          │                       │
       │                    │                          │                       │
       │  2. Auth Challenge │                          │                       │
       │ ◀──────────────────│                          │                       │
       │                    │                          │                       │
       │  3. Credentials    │                          │                       │
       │ ──────────────────▶│                          │                       │
       │                    │                          │                       │
       │  4. ID + Access    │                          │                       │
       │     Tokens         │                          │                       │
       │ ◀──────────────────│                          │                       │
       │                    │                          │                       │
       │  5. API Request    │                          │                       │
       │     + Bearer Token │                          │                       │
       │ ─────────────────────────────────────────────▶│                       │
       │                    │                          │                       │
       │                    │  6. Validate Token       │                       │
       │                    │ ◀────────────────────────│                       │
       │                    │                          │                       │
       │                    │  7. Token Valid          │                       │
       │                    │ ────────────────────────▶│                       │
       │                    │                          │                       │
       │                    │                          │  8. Forward Request   │
       │                    │                          │ ─────────────────────▶│
       │                    │                          │                       │
       │                    │                          │  9. Response          │
       │                    │                          │ ◀─────────────────────│
       │                    │                          │                       │
       │  10. API Response  │                          │                       │
       │ ◀─────────────────────────────────────────────│                       │
       │                    │                          │                       │
       ▼                    ▼                          ▼                       ▼
```

### Service-to-Service Authentication

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         MANAGED IDENTITY FLOW                                            │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  Backend Service        Azure AD                 Target Resource
       │                    │                          │
       │  1. Request Token  │                          │
       │     (No Creds!)    │                          │
       │ ──────────────────▶│                          │
       │                    │                          │
       │  2. Verify         │                          │
       │     Managed ID     │                          │
       │ ◀──────────────────│                          │
       │                    │                          │
       │  3. Access Token   │                          │
       │ ◀──────────────────│                          │
       │                    │                          │
       │  4. Access Resource│                          │
       │     + Token        │                          │
       │ ─────────────────────────────────────────────▶│
       │                    │                          │
       │  5. Validate &     │                          │
       │     Authorize      │                          │
       │ ◀─────────────────────────────────────────────│
       │                    │                          │
       ▼                    ▼                          ▼

  Benefits:
  • No credentials stored in code/config
  • Automatic key rotation
  • Centralized identity management
  • Easy RBAC integration
```

## Authorization

### Role-Based Access Control (RBAC)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              ROLE DEFINITIONS                                            │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────────────────────────────────────┐
  │  ROLE: Agent                                                                           │
  │  ─────────────────────────────────────────────────────────────────────────────────────│
  │  Permissions:                                                                          │
  │  ├── Claims:     Create, Read, Update (own)                                           │
  │  ├── Policies:   Read                                                                  │
  │  ├── Customers:  Read, Update (assigned)                                              │
  │  ├── Quotes:     Create, Read                                                          │
  │  └── Reports:    Read (own metrics)                                                   │
  └───────────────────────────────────────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────────────────────────────────────┐
  │  ROLE: Approver (Config Manager)                                                       │
  │  ─────────────────────────────────────────────────────────────────────────────────────│
  │  Permissions:                                                                          │
  │  ├── Config:     Read, Approve pending changes                                        │
  │  ├── Claims:     Read, Update, Approve (all)                                          │
  │  ├── AI Config:  Approve model/provider changes                                       │
  │  ├── Rating:     Approve factor changes                                               │
  │  └── Audit:      View approval history                                                │
  └───────────────────────────────────────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────────────────────────────────────┐
  │  ROLE: Administrator                                                                   │
  │  ─────────────────────────────────────────────────────────────────────────────────────│
  │  Permissions:                                                                          │
  │  ├── All Entities: Full CRUD                                                          │
  │  ├── AI Config:    Update providers, models, settings                                 │
  │  ├── Rating:       Update factors                                                      │
  │  ├── Costs:        View Azure/AWS cost reports                                        │
  │  ├── Users:        Manage roles                                                        │
  │  └── Audit:        View all logs                                                       │
  └───────────────────────────────────────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────────────────────────────────────┐
  │  ROLE: Viewer (Read-Only)                                                              │
  │  ─────────────────────────────────────────────────────────────────────────────────────│
  │  Permissions:                                                                          │
  │  ├── Config:     Read only                                                            │
  │  ├── Costs:      View reports                                                          │
  │  ├── Audit:      View logs                                                            │
  │  └── Pipeline:   View status (no trigger)                                             │
  └───────────────────────────────────────────────────────────────────────────────────────┘
```

### WS8 Admin Portal Permission Matrix

| Endpoint | Viewer | Config Manager | Approver | Admin |
|----------|--------|----------------|----------|-------|
| `GET /api/v1/config/ai/*` | ✓ | ✓ | ✓ | ✓ |
| `PUT /api/v1/config/ai/*` | ✗ | ✓ | ✗ | ✓ |
| `GET /api/v1/config/claims/*` | ✓ | ✓ | ✓ | ✓ |
| `PUT /api/v1/config/claims/*` | ✗ | ✓ | ✗ | ✓ |
| `GET /api/v1/costs/*` | ✓ | ✓ | ✓ | ✓ |
| `GET /api/v1/audit/*` | ✓ | ✓ | ✓ | ✓ |
| `GET /api/v1/approvals/*` | ✗ | ✗ | ✓ | ✓ |
| `POST /api/v1/approvals/*/approve` | ✗ | ✗ | ✓ | ✓ |
| `GET /api/v1/users/*` | ✗ | ✗ | ✗ | ✓ |
| `PUT /api/v1/users/*` | ✗ | ✗ | ✗ | ✓ |

### Maker-Checker Workflow

Configuration changes requiring approval:
- `ai_config` - AI provider/model changes
- `claims_rules` - Claims processing rules
- `rating_config` - Rating factor updates
- `policy_config` - Policy templates

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                           MAKER-CHECKER APPROVAL FLOW                                     │
└──────────────────────────────────────────────────────────────────────────────────────────┘

  Config Manager              Admin Portal                    Approver
       │                          │                              │
       │  1. Submit config change │                              │
       │     (maker)              │                              │
       │ ────────────────────────▶│                              │
       │                          │                              │
       │                          │  2. Store as "pending"       │
       │                          │     Create approval request  │
       │                          │─────────┐                    │
       │                          │         │                    │
       │                          │◀────────┘                    │
       │                          │                              │
       │                          │  3. Notify approver          │
       │                          │ ────────────────────────────▶│
       │                          │                              │
       │                          │  4. Review + Approve/Reject  │
       │                          │     (checker)                │
       │                          │ ◀────────────────────────────│
       │                          │                              │
       │                          │  5. If approved: Apply config│
       │                          │     Update audit log         │
       │                          │─────────┐                    │
       │                          │         │                    │
       │                          │◀────────┘                    │
       │                          │                              │
       │  6. Notification         │                              │
       │ ◀────────────────────────│                              │
       │                          │                              │
       ▼                          ▼                              ▼
```

### API Permission Matrix (Claims Data API)

| Endpoint | Agent | Supervisor | Admin |
|----------|-------|------------|-------|
| `POST /claims/fnol` | ✓ | ✓ | ✓ |
| `GET /claims/*` | ✓ (own) | ✓ (all) | ✓ |
| `PUT /claims/*/approve` | ✗ | ✓ | ✓ |
| `GET /policies` | ✓ | ✓ | ✓ |
| `POST /rating/quote` | ✓ | ✓ | ✓ |
| `PUT /rating/factors` | ✗ | ✗ | ✓ |
| `POST /pipeline/trigger` | ✓ | ✓ | ✓ |

## Data Protection

### Encryption Standards

| Data State | Encryption | Key Management |
|------------|------------|----------------|
| At Rest | AES-256 | Azure Key Vault |
| In Transit | TLS 1.3 | Azure-managed |
| Backups | AES-256 | Customer-managed key |

### Sensitive Data Handling

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         SENSITIVE DATA CLASSIFICATION                                    │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────┐
  │     PUBLIC       │   • Marketing content
  │     ──────────   │   • Product descriptions
  │     Handling:    │   • General FAQ
  │     Standard     │
  └──────────────────┘

  ┌──────────────────┐
  │    INTERNAL      │   • Policy numbers
  │    ──────────    │   • Claim status
  │    Handling:     │   • Premium amounts
  │    Controlled    │
  └──────────────────┘

  ┌──────────────────┐
  │  CONFIDENTIAL    │   • Customer names
  │  ────────────    │   • Addresses
  │  Handling:       │   • Phone numbers
  │  Encrypted +     │   • Email addresses
  │  Access Control  │
  └──────────────────┘

  ┌──────────────────┐
  │   RESTRICTED     │   • SSN
  │   ──────────     │   • Driver license #
  │   Handling:      │   • Bank accounts
  │   Encrypted +    │   • Medical records
  │   Masked +       │
  │   Audit Logged   │
  └──────────────────┘
```

### Data Masking Examples

```
Original Data              Masked (Logs/UI)
─────────────────────      ─────────────────────
john.doe@email.com    →    j***@e***.com
555-123-4567          →    ***-***-4567
123-45-6789 (SSN)     →    ***-**-6789
4111-1111-1111-1111   →    ****-****-****-1111
```

## Secrets Management

### Environment-Based Configuration

For local development and AWS deployment, secrets are managed via environment variables:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         ENVIRONMENT VARIABLES (.env)                                     │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  Required for AI Services:
  ├── ANTHROPIC_API_KEY         ← Claude API key (default AI provider)
  ├── OPENAI_API_KEY            ← OpenAI API key (fallback provider)
  └── AZURE_OPENAI_ENDPOINT     ← Azure OpenAI endpoint (optional)

  Application Configuration:
  ├── ENVIRONMENT               ← dev | staging | prod
  ├── DEBUG                     ← true | false
  ├── LOG_LEVEL                 ← INFO | DEBUG | WARNING
  └── CORS_ORIGINS              ← ["http://localhost:8080", "http://localhost:8081"]

  Optional Azure Services:
  ├── COSMOS_DB_ENDPOINT        ← Cosmos DB endpoint
  ├── COSMOS_DB_KEY             ← Cosmos DB access key
  ├── AZURE_STORAGE_CONNECTION  ← Blob storage connection string
  └── DATAVERSE_URL             ← D365 Dataverse URL

  WS8 Admin Security:
  ├── JWT_SECRET                ← JWT signing secret (HS256)
  └── JWT_EXPIRATION            ← Token expiration (default: 24h)
```

### Azure Key Vault Integration (Optional)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              KEY VAULT ARCHITECTURE                                      │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────────────────┐
  │                            Azure Key Vault                                           │
  │  ┌───────────────────────────────────────────────────────────────────────────────┐  │
  │  │  SECRETS                                                                       │  │
  │  │  ├── ANTHROPIC-API-KEY                 ← Claude API key (primary)             │  │
  │  │  ├── OPENAI-API-KEY                    ← OpenAI API key (fallback)            │  │
  │  │  ├── AZURE-OPENAI-KEY                  ← Azure OpenAI key (optional)          │  │
  │  │  ├── COSMOS-DB-KEY                     ← Database access key                   │  │
  │  │  ├── SERVICE-BUS-CONNECTION            ← Message queue connection              │  │
  │  │  ├── STORAGE-CONNECTION                ← Blob storage access                   │  │
  │  │  ├── DATAVERSE-CLIENT-SECRET           ← D365 auth secret                      │  │
  │  │  ├── JWT-SECRET                        ← WS8 Admin JWT signing key            │  │
  │  │  └── EIS-WEBHOOK-SECRET                ← Webhook signature key                 │  │
  │  └───────────────────────────────────────────────────────────────────────────────┘  │
  │                                                                                      │
  │  ┌───────────────────────────────────────────────────────────────────────────────┐  │
  │  │  ACCESS POLICIES                                                               │  │
  │  │  ├── WS6-Agent-Pipeline (MI)  → Get, List (AI keys)                           │  │
  │  │  ├── WS7-DocGen (MI)          → Get, List (AI keys)                           │  │
  │  │  ├── WS8-Admin (MI)           → Get, List (JWT secret)                        │  │
  │  │  ├── GitHub-Actions (SPN)     → Get, List, Set                                │  │
  │  │  └── Admin-Group (AAD)        → All permissions                               │  │
  │  └───────────────────────────────────────────────────────────────────────────────┘  │
  └─────────────────────────────────────────────────────────────────────────────────────┘
```

### AWS Secrets Manager (Production)

For AWS AppRunner deployments:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         AWS SECRETS MANAGER                                              │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  eis-dynamics/prod/ai-keys:
  ├── ANTHROPIC_API_KEY
  └── OPENAI_API_KEY

  eis-dynamics/prod/jwt:
  └── JWT_SECRET

  Access via IAM Role attached to AppRunner service
```

### Secret Rotation

| Secret Type | Rotation Period | Method |
|-------------|-----------------|--------|
| API Keys | 90 days | Manual + Alert |
| DB Keys | 60 days | Automated |
| Client Secrets | 180 days | Automated |
| TLS Certificates | 365 days | Azure-managed |

## Audit & Compliance

### Audit Logging

```json
{
  "timestamp": "2024-06-15T14:30:00Z",
  "event_type": "claim.created",
  "actor": {
    "user_id": "user_abc123",
    "email": "agent@company.com",
    "role": "Agent",
    "ip_address": "192.168.1.100"
  },
  "resource": {
    "type": "claim",
    "id": "CLM-2024-00001"
  },
  "action": "create",
  "result": "success",
  "details": {
    "policy_id": "POL-2024-001",
    "fraud_score": 0.12
  },
  "request_id": "req_xyz789"
}
```

### Compliance Controls

| Requirement | Control | Evidence |
|-------------|---------|----------|
| Data Encryption | AES-256 at rest, TLS 1.3 in transit | Azure compliance reports |
| Access Control | RBAC, MFA | Azure AD logs |
| Audit Trail | All actions logged | Log Analytics |
| Data Retention | 7-year retention | Storage policies |
| Incident Response | 24-hour SLA | Runbook documentation |

## Security Monitoring

### Alert Triggers

| Event | Severity | Response |
|-------|----------|----------|
| Failed auth (5+ attempts) | High | Account lockout |
| Unusual API pattern | Medium | Investigation |
| High fraud score (>0.8) | High | SIU notification |
| Key Vault access denied | Critical | Security team page |
| DDoS detected | Critical | Auto-mitigation |
