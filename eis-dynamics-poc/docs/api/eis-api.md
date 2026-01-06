# EIS Pet Insurance Mock API Reference (WS3)

Base URL: `/api/v1`

## Overview

The EIS Mock API simulates the EIS Suite pet insurance core system, providing endpoints for pet policies, pets, claims, and pet owners. This enables development and testing without a live EIS connection.

## Endpoints

### Pet Policies

#### List Pet Policies

Retrieve all pet policies with optional filtering.

```
GET /eis/policies
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter by status (active, expired, cancelled) |
| customer_id | string | Filter by pet owner |
| plan_type | string | Filter by plan (accident_only, accident_illness, comprehensive) |
| limit | integer | Max results (default: 50) |
| offset | integer | Pagination offset |

#### Example Request

```bash
curl "http://localhost:8002/api/v1/eis/policies?status=active&limit=10"
```

#### Response (200 OK)

```json
{
  "policies": [
    {
      "policy_id": "POL-PET-2024-001",
      "policy_number": "PET-IL-2024-00001",
      "customer_id": "CUST-001",
      "pet_owner_name": "John Smith",
      "plan_type": "accident_illness",
      "status": "active",
      "effective_date": "2024-01-01",
      "expiration_date": "2025-01-01",
      "total_premium": 637.62,
      "annual_limit": 10000.00,
      "deductible": 250.00,
      "reimbursement_pct": 80,
      "pets": [
        {
          "pet_id": "PET-001",
          "name": "Max",
          "species": "dog",
          "breed": "Golden Retriever"
        }
      ]
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

---

#### Get Pet Policy

Retrieve a single pet policy by ID.

```
GET /eis/policies/{policy_id}
```

#### Response (200 OK)

```json
{
  "policy_id": "POL-PET-2024-001",
  "policy_number": "PET-IL-2024-00001",
  "customer_id": "CUST-001",
  "pet_owner_name": "John Smith",
  "plan_type": "accident_illness",
  "status": "active",
  "effective_date": "2024-01-01",
  "expiration_date": "2025-01-01",
  "total_premium": 637.62,
  "annual_limit": 10000.00,
  "deductible": 250.00,
  "reimbursement_pct": 80,
  "billing_frequency": "monthly",
  "payment_method": "autopay",
  "pets": [
    {
      "pet_id": "PET-001",
      "name": "Max",
      "species": "dog",
      "breed": "Golden Retriever",
      "date_of_birth": "2019-03-15",
      "gender": "male",
      "microchip_id": "985121012345678",
      "spayed_neutered": true,
      "weight_lbs": 72,
      "color": "golden"
    }
  ],
  "coverages": [
    {
      "coverage_id": "COV-001",
      "coverage_type": "accident",
      "limit": 10000.00,
      "waiting_period_days": 3,
      "premium": 150.00
    },
    {
      "coverage_id": "COV-002",
      "coverage_type": "illness",
      "limit": 10000.00,
      "waiting_period_days": 14,
      "premium": 300.00
    },
    {
      "coverage_id": "COV-003",
      "coverage_type": "hereditary",
      "limit": 10000.00,
      "waiting_period_days": 14,
      "premium": 100.00
    }
  ],
  "add_ons": [],
  "discounts": [
    {"type": "spayed_neutered", "rate": 0.05, "amount": 33.84},
    {"type": "microchipped", "rate": 0.03, "amount": 20.30}
  ]
}
```

---

### Pets

#### List Pets

Retrieve all pets.

```
GET /eis/pets
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| species | string | Filter by species (dog, cat) |
| breed | string | Filter by breed |
| policy_id | string | Filter by policy |

#### Response (200 OK)

```json
{
  "pets": [
    {
      "pet_id": "PET-001",
      "name": "Max",
      "species": "dog",
      "breed": "Golden Retriever",
      "date_of_birth": "2019-03-15",
      "gender": "male",
      "policy_id": "POL-PET-2024-001",
      "customer_id": "CUST-001"
    },
    {
      "pet_id": "PET-002",
      "name": "Whiskers",
      "species": "cat",
      "breed": "Maine Coon",
      "date_of_birth": "2020-08-22",
      "gender": "female",
      "policy_id": "POL-PET-2024-002",
      "customer_id": "CUST-002"
    }
  ],
  "total": 2
}
```

---

#### Get Pet

Retrieve a single pet by ID.

```
GET /eis/pets/{pet_id}
```

#### Response (200 OK)

```json
{
  "pet_id": "PET-001",
  "name": "Max",
  "species": "dog",
  "breed": "Golden Retriever",
  "breed_group": "Sporting",
  "date_of_birth": "2019-03-15",
  "age_years": 5,
  "gender": "male",
  "microchip_id": "985121012345678",
  "spayed_neutered": true,
  "weight_lbs": 72,
  "color": "golden",
  "policy_id": "POL-PET-2024-001",
  "customer_id": "CUST-001",
  "pre_existing_conditions": [],
  "vaccination_status": "current",
  "last_vet_visit": "2024-06-15"
}
```

---

### Pet Owners (Customers)

#### List Pet Owners

Retrieve all pet owners.

```
GET /eis/customers
```

#### Response (200 OK)

```json
{
  "customers": [
    {
      "customer_id": "CUST-001",
      "first_name": "John",
      "last_name": "Smith",
      "email": "john.smith@example.com",
      "phone": "555-123-4567",
      "address": "456 Oak Avenue, Chicago, IL 60601",
      "customer_type": "individual",
      "created_at": "2024-01-15T10:30:00Z",
      "pets_count": 1,
      "active_policies": 1
    }
  ],
  "total": 1
}
```

---

#### Get Pet Owner

Retrieve a single pet owner by ID.

```
GET /eis/customers/{customer_id}
```

#### Response (200 OK)

```json
{
  "customer_id": "CUST-001",
  "first_name": "John",
  "last_name": "Smith",
  "email": "john.smith@example.com",
  "phone": "555-123-4567",
  "address": "456 Oak Avenue",
  "city": "Chicago",
  "state": "IL",
  "zip_code": "60601",
  "customer_type": "individual",
  "date_of_birth": "1985-03-15",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-06-01T09:00:00Z"
}
```

---

#### Get Pet Owner's Pets

Retrieve all pets for a pet owner.

```
GET /eis/customers/{customer_id}/pets
```

#### Response (200 OK)

```json
{
  "pets": [
    {
      "pet_id": "PET-001",
      "name": "Max",
      "species": "dog",
      "breed": "Golden Retriever",
      "age_years": 5,
      "policy_id": "POL-PET-2024-001",
      "policy_status": "active"
    }
  ],
  "total": 1
}
```

---

#### Get Pet Owner's Policies

Retrieve all policies for a pet owner.

```
GET /eis/customers/{customer_id}/policies
```

#### Response (200 OK)

```json
{
  "policies": [
    {
      "policy_id": "POL-PET-2024-001",
      "policy_number": "PET-IL-2024-00001",
      "plan_type": "accident_illness",
      "status": "active",
      "effective_date": "2024-01-01",
      "expiration_date": "2025-01-01",
      "total_premium": 637.62,
      "pets_covered": 1
    }
  ],
  "total": 1
}
```

---

#### Get Pet Owner's Claims

Retrieve all claims for a pet owner.

```
GET /eis/customers/{customer_id}/claims
```

#### Response (200 OK)

```json
{
  "claims": [
    {
      "claim_id": "CLM-PET-2024-001",
      "claim_number": "CLM-PET-2024-00001",
      "policy_id": "POL-PET-2024-001",
      "pet_id": "PET-001",
      "pet_name": "Max",
      "date_of_service": "2024-06-15",
      "condition_type": "accident",
      "diagnosis": "Torn CCL",
      "status": "under_review",
      "amount_billed": 4500.00,
      "amount_approved": 4500.00,
      "estimated_payout": 3400.00,
      "fraud_score": 0.15
    }
  ],
  "total": 1
}
```

---

### Pet Claims (EIS Source)

#### Get Claim from EIS

Retrieve claim details from EIS system.

```
GET /eis/claims/{claim_id}
```

#### Response (200 OK)

```json
{
  "claim_id": "CLM-PET-2024-001",
  "claim_number": "CLM-PET-2024-00001",
  "policy_id": "POL-PET-2024-001",
  "pet_id": "PET-001",
  "pet_name": "Max",
  "pet_species": "dog",
  "pet_breed": "Golden Retriever",
  "date_of_service": "2024-06-15",
  "date_reported": "2024-06-15T14:30:00Z",
  "status": "under_review",
  "condition_type": "accident",
  "diagnosis": "Torn CCL (Cranial Cruciate Ligament)",
  "treatment": "TPLO Surgery",
  "vet_provider_id": "VET-001",
  "vet_clinic_name": "Happy Paws Veterinary Clinic",
  "amount_billed": 4500.00,
  "amount_approved": 4500.00,
  "amount_paid": 0.00,
  "deductible_applied": 250.00,
  "reimbursement_rate": 0.80,
  "estimated_payout": 3400.00,
  "fraud_score": 0.15,
  "pre_existing_flag": false,
  "adjuster_id": null
}
```

---

### Vet Providers

#### List Vet Providers

Retrieve all registered vet providers.

```
GET /eis/vet-providers
```

#### Response (200 OK)

```json
{
  "providers": [
    {
      "provider_id": "VET-001",
      "clinic_name": "Happy Paws Veterinary Clinic",
      "address": "123 Pet Street, Chicago, IL 60601",
      "phone": "312-555-0100",
      "email": "info@happypaws.vet",
      "license_number": "IL-VET-12345",
      "is_preferred": true,
      "fraud_flag": false,
      "claims_processed": 45
    }
  ],
  "total": 1
}
```

---

### Webhooks (Simulation)

#### Trigger Policy Webhook

Simulate an EIS pet policy webhook event.

```
POST /eis/webhooks/policy
```

#### Request Body

```json
{
  "event_type": "policy.created",
  "policy_id": "POL-PET-2024-002",
  "policy_number": "PET-IL-2024-00002",
  "timestamp": "2024-06-15T15:00:00Z"
}
```

#### Response (202 Accepted)

```json
{
  "message": "Webhook received",
  "event_id": "evt_abc123",
  "status": "queued"
}
```

---

#### Trigger Claim Webhook

Simulate an EIS pet claim webhook event.

```
POST /eis/webhooks/claim
```

#### Request Body

```json
{
  "event_type": "claim.status_changed",
  "claim_id": "CLM-PET-2024-001",
  "pet_name": "Max",
  "previous_status": "submitted",
  "new_status": "under_review",
  "timestamp": "2024-06-15T16:00:00Z"
}
```

---

## Sync API

### Trigger Sync

Manually trigger a sync operation.

```
POST /sync/trigger
```

#### Request Body

```json
{
  "entity_type": "pet_policy|pet_claim|pet|customer",
  "direction": "eis_to_d365|d365_to_eis",
  "entity_id": "string (optional) - specific entity to sync"
}
```

#### Response (202 Accepted)

```json
{
  "sync_id": "sync_abc123",
  "entity_type": "pet_policy",
  "direction": "eis_to_d365",
  "status": "in_progress",
  "started_at": "2024-06-15T14:30:00Z"
}
```

---

### Get Sync Status

Check status of a sync operation.

```
GET /sync/status/{sync_id}
```

#### Response (200 OK)

```json
{
  "sync_id": "sync_abc123",
  "entity_type": "pet_policy",
  "direction": "eis_to_d365",
  "status": "completed",
  "started_at": "2024-06-15T14:30:00Z",
  "completed_at": "2024-06-15T14:30:45Z",
  "entities_processed": 50,
  "entities_succeeded": 49,
  "entities_failed": 1,
  "errors": [
    {
      "entity_id": "POL-PET-2024-050",
      "error": "Dataverse conflict - pet owner not found"
    }
  ]
}
```

---

## Mock Data

The EIS Mock API comes pre-populated with sample pet insurance data for testing:

| Entity | Count | ID Pattern |
|--------|-------|------------|
| Pet Owners | 10 | CUST-001 to CUST-010 |
| Pets | 15 | PET-001 to PET-015 |
| Pet Policies | 12 | POL-PET-2024-001 to POL-PET-2024-012 |
| Pet Claims | 8 | CLM-PET-2024-001 to CLM-PET-2024-008 |
| Vet Providers | 5 | VET-001 to VET-005 |

### Sample Pets

| Pet ID | Name | Species | Breed | Age |
|--------|------|---------|-------|-----|
| PET-001 | Max | Dog | Golden Retriever | 5 |
| PET-002 | Whiskers | Cat | Maine Coon | 4 |
| PET-003 | Bella | Dog | French Bulldog | 3 |
| PET-004 | Luna | Dog | Labrador Retriever | 2 |
| PET-005 | Charlie | Cat | Domestic Shorthair | 6 |

### Reset Mock Data

Reset mock data to default state (development only).

```
POST /eis/admin/reset
```

---

## Error Codes

| Code | Description |
|------|-------------|
| POLICY_NOT_FOUND | Policy ID does not exist |
| PET_NOT_FOUND | Pet ID does not exist |
| CUSTOMER_NOT_FOUND | Customer ID does not exist |
| CLAIM_NOT_FOUND | Claim ID does not exist |
| VET_PROVIDER_NOT_FOUND | Vet provider ID does not exist |
| SYNC_IN_PROGRESS | Another sync is already running |
| WEBHOOK_INVALID | Invalid webhook signature |
