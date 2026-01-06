"""
PetInsure360 - Policies API
Endpoints for policy creation and management
"""

import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException
from app.models.schemas import PolicyCreate, PolicyResponse

router = APIRouter()

# Plan configurations
PLAN_CONFIG = {
    "Basic": {
        "monthly_premium": 29.99,
        "annual_deductible": 500.0,
        "coverage_limit": 5000.0,
        "reimbursement_percentage": 70.0,
        "waiting_period_days": 14
    },
    "Standard": {
        "monthly_premium": 49.99,
        "annual_deductible": 250.0,
        "coverage_limit": 10000.0,
        "reimbursement_percentage": 80.0,
        "waiting_period_days": 14
    },
    "Premium": {
        "monthly_premium": 79.99,
        "annual_deductible": 100.0,
        "coverage_limit": 20000.0,
        "reimbursement_percentage": 90.0,
        "waiting_period_days": 7
    },
    "Unlimited": {
        "monthly_premium": 99.99,
        "annual_deductible": 0.0,
        "coverage_limit": 999999.0,
        "reimbursement_percentage": 100.0,
        "waiting_period_days": 0
    }
}

@router.post("/", response_model=PolicyResponse)
async def create_policy(policy: PolicyCreate, request: Request):
    """
    Create a new insurance policy.

    Writes policy data to Azure Data Lake Storage for ETL processing.
    """
    # Generate policy ID and number
    policy_id = f"POL-{uuid.uuid4().hex[:8].upper()}"
    policy_number = f"PI-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    # Get plan configuration
    plan_config = PLAN_CONFIG.get(policy.plan_name.value, PLAN_CONFIG["Basic"])

    # Calculate dates
    effective_date = datetime.utcnow().date()
    expiration_date = effective_date + timedelta(days=365)

    # Prepare data for storage
    policy_data = {
        "policy_id": policy_id,
        "policy_number": policy_number,
        "customer_id": policy.customer_id,
        "pet_id": policy.pet_id,
        "plan_name": policy.plan_name.value,
        "monthly_premium": plan_config["monthly_premium"],
        "annual_deductible": plan_config["annual_deductible"],
        "coverage_limit": plan_config["coverage_limit"],
        "reimbursement_percentage": plan_config["reimbursement_percentage"],
        "effective_date": effective_date.isoformat(),
        "expiration_date": expiration_date.isoformat(),
        "status": "Active",
        "payment_method": policy.payment_method,
        "payment_frequency": policy.payment_frequency,
        "waiting_period_days": plan_config["waiting_period_days"],
        "includes_wellness": policy.includes_wellness,
        "includes_dental": policy.includes_dental,
        "includes_behavioral": policy.includes_behavioral,
        "cancellation_date": None,
        "renewal_count": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    # Write to ADLS
    storage = request.app.state.storage
    await storage.write_json("policies", policy_data, policy_id)

    # Add to in-memory insights data for real-time BI display
    insights = request.app.state.insights
    insights.add_policy(policy_data)

    # Emit WebSocket event
    sio = request.app.state.sio
    await sio.emit('policy_created', {
        'policy_id': policy_id,
        'policy_number': policy_number,
        'customer_id': policy.customer_id,
        'plan_name': policy.plan_name.value,
        'monthly_premium': plan_config["monthly_premium"],
        'timestamp': datetime.utcnow().isoformat()
    })

    # Notify customer room
    await sio.emit('policy_update', {
        'type': 'new_policy',
        'policy_id': policy_id,
        'policy_number': policy_number,
        'status': 'Active'
    }, room=f"customer_{policy.customer_id}")

    return PolicyResponse(
        policy_id=policy_id,
        policy_number=policy_number,
        customer_id=policy.customer_id,
        pet_id=policy.pet_id,
        plan_name=policy.plan_name.value,
        monthly_premium=plan_config["monthly_premium"],
        annual_deductible=plan_config["annual_deductible"],
        coverage_limit=plan_config["coverage_limit"],
        effective_date=effective_date,
        expiration_date=expiration_date,
        created_at=datetime.utcnow(),
        message=f"Policy {policy_number} created successfully"
    )

@router.get("/customer/{customer_id}")
async def get_customer_policies(customer_id: str, request: Request):
    """Get all policies for a customer."""
    insights = request.app.state.insights
    policies_list = insights.get_customer_policies(customer_id)

    return {
        "customer_id": customer_id,
        "policies": policies_list,
        "count": len(policies_list)
    }


@router.get("/pet/{pet_id}")
async def get_pet_policies(pet_id: str, request: Request):
    """Get all policies for a specific pet."""
    insights = request.app.state.insights
    all_policies = insights.get_all_policies()

    # Filter policies for this pet
    pet_policies = [p for p in all_policies if str(p.get('pet_id', '')) == pet_id]

    return {
        "pet_id": pet_id,
        "policies": pet_policies,
        "count": len(pet_policies)
    }


@router.get("/validate/{policy_id}/{pet_id}")
async def validate_policy_pet(policy_id: str, pet_id: str, request: Request):
    """
    Validate that a policy belongs to a specific pet.
    Returns validation result with policy details if valid.
    """
    insights = request.app.state.insights
    all_policies = insights.get_all_policies()

    # Find the policy
    policy = next((p for p in all_policies if str(p.get('policy_id', '')) == policy_id), None)

    if not policy:
        return {
            "valid": False,
            "error": "Policy not found",
            "policy_id": policy_id,
            "pet_id": pet_id
        }

    policy_pet_id = str(policy.get('pet_id', ''))
    is_valid = policy_pet_id == pet_id

    return {
        "valid": is_valid,
        "policy_id": policy_id,
        "pet_id": pet_id,
        "policy_pet_id": policy_pet_id,
        "policy_status": policy.get('status', 'Unknown'),
        "error": None if is_valid else f"Policy belongs to pet {policy_pet_id}, not {pet_id}"
    }


@router.get("/{policy_id}")
async def get_policy(policy_id: str, request: Request):
    """Get policy details."""
    return {
        "policy_id": policy_id,
        "message": "Query policy from Gold layer (not implemented in demo)"
    }

@router.get("/plans/available")
async def get_available_plans():
    """Get available insurance plans and their configurations."""
    return {
        "plans": [
            {
                "name": name,
                "monthly_premium": config["monthly_premium"],
                "annual_deductible": config["annual_deductible"],
                "coverage_limit": config["coverage_limit"],
                "reimbursement_percentage": config["reimbursement_percentage"],
                "waiting_period_days": config["waiting_period_days"]
            }
            for name, config in PLAN_CONFIG.items()
        ]
    }
