"""
PetInsure360 - Customers API
Endpoints for customer registration and management
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from app.models.schemas import CustomerCreate, CustomerResponse

router = APIRouter()

# Demo user data - exported for auto-seeding on startup
DEMO_USERS = [
    {"customer_id": "DEMO-001", "first_name": "Demo", "last_name": "User", "email": "demo@demologin.com", "phone": "(555) 100-0001", "city": "Austin", "state": "TX", "zip_code": "78701", "customer_since": "2024-01-01"},
    {"customer_id": "DEMO-002", "first_name": "Demo", "last_name": "One", "email": "demo1@demologin.com", "phone": "(555) 100-0002", "city": "Dallas", "state": "TX", "zip_code": "75201", "customer_since": "2024-03-15"},
    {"customer_id": "DEMO-003", "first_name": "Demo", "last_name": "Two", "email": "demo2@demologin.com", "phone": "(555) 100-0003", "city": "Houston", "state": "TX", "zip_code": "77001", "customer_since": "2024-06-01"},
]

DEMO_PETS = [
    {"pet_id": "PET-DEMO-001", "customer_id": "DEMO-001", "pet_name": "Buddy", "species": "Dog", "breed": "Golden Retriever", "gender": "Male", "date_of_birth": "2020-03-15", "weight_lbs": 75, "color": "Golden", "is_spayed_neutered": True},
    {"pet_id": "PET-DEMO-002", "customer_id": "DEMO-001", "pet_name": "Whiskers", "species": "Cat", "breed": "Persian", "gender": "Female", "date_of_birth": "2021-07-20", "weight_lbs": 12, "color": "White", "is_spayed_neutered": True},
    {"pet_id": "PET-DEMO-003", "customer_id": "DEMO-002", "pet_name": "Max", "species": "Dog", "breed": "German Shepherd", "gender": "Male", "date_of_birth": "2019-08-10", "weight_lbs": 85, "color": "Black & Tan", "is_spayed_neutered": True},
    {"pet_id": "PET-DEMO-004", "customer_id": "DEMO-002", "pet_name": "Luna", "species": "Cat", "breed": "Siamese", "gender": "Female", "date_of_birth": "2022-02-14", "weight_lbs": 10, "color": "Seal Point", "is_spayed_neutered": True},
    {"pet_id": "PET-DEMO-005", "customer_id": "DEMO-003", "pet_name": "Charlie", "species": "Dog", "breed": "Labrador", "gender": "Male", "date_of_birth": "2021-11-05", "weight_lbs": 70, "color": "Chocolate", "is_spayed_neutered": True},
]

DEMO_POLICIES = [
    {"policy_id": "POL-DEMO-001", "customer_id": "DEMO-001", "pet_id": "PET-DEMO-001", "plan_type": "Premium Plus", "coverage_type": "Accident & Illness", "monthly_premium": 89.99, "annual_deductible": 250, "reimbursement_percentage": 90, "annual_limit": 15000},
    {"policy_id": "POL-DEMO-002", "customer_id": "DEMO-001", "pet_id": "PET-DEMO-002", "plan_type": "Standard", "coverage_type": "Accident & Illness", "monthly_premium": 45.99, "annual_deductible": 500, "reimbursement_percentage": 80, "annual_limit": 10000},
    {"policy_id": "POL-DEMO-003", "customer_id": "DEMO-002", "pet_id": "PET-DEMO-003", "plan_type": "Premium", "coverage_type": "Accident & Illness", "monthly_premium": 79.99, "annual_deductible": 300, "reimbursement_percentage": 85, "annual_limit": 12000},
    {"policy_id": "POL-DEMO-004", "customer_id": "DEMO-003", "pet_id": "PET-DEMO-005", "plan_type": "Basic", "coverage_type": "Accident Only", "monthly_premium": 29.99, "annual_deductible": 750, "reimbursement_percentage": 70, "annual_limit": 5000},
]

@router.post("/", response_model=CustomerResponse)
async def create_customer(customer: CustomerCreate, request: Request):
    """
    Register a new customer.

    Writes customer data to Azure Data Lake Storage for ETL processing.
    """
    # Generate customer ID
    customer_id = f"CUST-{uuid.uuid4().hex[:8].upper()}"

    # Get address from helper method (supports both 'address' and 'address_line1')
    actual_address = customer.get_address()

    # Prepare data for storage
    customer_dict = customer.model_dump(exclude={'address'})  # Exclude duplicate
    customer_data = {
        "customer_id": customer_id,
        **customer_dict,
        "address_line1": actual_address,  # Use the resolved address
        "customer_since": datetime.utcnow().date().isoformat(),
        "customer_segment": "New",
        "lifetime_value": 0.0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    # Write to ADLS
    storage = request.app.state.storage
    await storage.write_json("customers", customer_data, customer_id)

    # Add to in-memory insights data for real-time BI display
    insights = request.app.state.insights
    insights.add_customer(customer_data)

    # Emit WebSocket event
    sio = request.app.state.sio
    await sio.emit('customer_created', {
        'customer_id': customer_id,
        'name': f"{customer.first_name} {customer.last_name}",
        'timestamp': datetime.utcnow().isoformat()
    })

    return CustomerResponse(
        customer_id=customer_id,
        first_name=customer.first_name,
        last_name=customer.last_name,
        email=customer.email,
        phone=customer.phone,
        city=customer.city,
        state=customer.state,
        created_at=datetime.utcnow(),
        message=f"Customer {customer_id} registered successfully"
    )

@router.get("/lookup")
async def lookup_customer_by_email(email: str, request: Request):
    """
    Look up a customer by email address (for login).
    Searches in-memory insights data and demo users.
    """
    insights = request.app.state.insights

    # First check DEMO_USERS directly (guaranteed to exist)
    for demo_user in DEMO_USERS:
        if demo_user.get('email', '').lower() == email.lower():
            # Return demo user with associated pets and policies
            pets = [p for p in DEMO_PETS if p['customer_id'] == demo_user['customer_id']]
            policies = [p for p in DEMO_POLICIES if p['customer_id'] == demo_user['customer_id']]
            return {
                "customer": {
                    **demo_user,
                    "full_name": f"{demo_user['first_name']} {demo_user['last_name']}",
                    "pets": pets,
                    "policies": policies
                },
                "message": "Customer found (demo user)"
            }

    # Then check insights data
    customers = insights.get_customer_360(limit=10000)

    # Find customer by email
    for customer in customers:
        if customer.get('email', '').lower() == email.lower():
            return {
                "customer": customer,
                "message": "Customer found"
            }

    raise HTTPException(status_code=404, detail="No account found with this email. Please register first.")


@router.post("/seed-demo")
async def seed_demo_data(request: Request):
    """
    Seed demo users with pets and policies for testing.
    Creates DEMO-001, DEMO-002, DEMO-003 with associated data.
    """
    insights = request.app.state.insights
    storage = request.app.state.storage

    demo_data = {
        "DEMO-001": {
            "customer": {
                "customer_id": "DEMO-001",
                "first_name": "Demo",
                "last_name": "User",
                "email": "demo@demologin.com",
                "phone": "(555) 100-0001",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78701",
                "customer_since": "2024-01-01"
            },
            "pets": [
                {"pet_id": "PET-DEMO-001", "customer_id": "DEMO-001", "pet_name": "Buddy", "species": "Dog", "breed": "Golden Retriever", "gender": "Male", "date_of_birth": "2020-03-15", "weight_lbs": 75, "color": "Golden", "is_spayed_neutered": True},
                {"pet_id": "PET-DEMO-002", "customer_id": "DEMO-001", "pet_name": "Whiskers", "species": "Cat", "breed": "Persian", "gender": "Female", "date_of_birth": "2021-07-20", "weight_lbs": 12, "color": "White", "is_spayed_neutered": True}
            ],
            "policies": [
                {"policy_id": "POL-DEMO-001", "customer_id": "DEMO-001", "pet_id": "PET-DEMO-001", "plan_type": "Premium Plus", "coverage_type": "Accident & Illness", "monthly_premium": 89.99, "annual_deductible": 250, "reimbursement_percentage": 90, "annual_limit": 15000},
                {"policy_id": "POL-DEMO-002", "customer_id": "DEMO-001", "pet_id": "PET-DEMO-002", "plan_type": "Standard", "coverage_type": "Accident & Illness", "monthly_premium": 45.99, "annual_deductible": 500, "reimbursement_percentage": 80, "annual_limit": 10000}
            ]
        },
        "DEMO-002": {
            "customer": {
                "customer_id": "DEMO-002",
                "first_name": "Demo",
                "last_name": "One",
                "email": "demo1@demologin.com",
                "phone": "(555) 100-0002",
                "city": "Dallas",
                "state": "TX",
                "zip_code": "75201",
                "customer_since": "2024-03-15"
            },
            "pets": [
                {"pet_id": "PET-DEMO-003", "customer_id": "DEMO-002", "pet_name": "Max", "species": "Dog", "breed": "German Shepherd", "gender": "Male", "date_of_birth": "2019-08-10", "weight_lbs": 85, "color": "Black & Tan", "is_spayed_neutered": True},
                {"pet_id": "PET-DEMO-004", "customer_id": "DEMO-002", "pet_name": "Luna", "species": "Cat", "breed": "Siamese", "gender": "Female", "date_of_birth": "2022-02-14", "weight_lbs": 10, "color": "Seal Point", "is_spayed_neutered": True}
            ],
            "policies": [
                {"policy_id": "POL-DEMO-003", "customer_id": "DEMO-002", "pet_id": "PET-DEMO-003", "plan_type": "Premium", "coverage_type": "Accident & Illness", "monthly_premium": 79.99, "annual_deductible": 300, "reimbursement_percentage": 85, "annual_limit": 12000}
            ]
        },
        "DEMO-003": {
            "customer": {
                "customer_id": "DEMO-003",
                "first_name": "Demo",
                "last_name": "Two",
                "email": "demo2@demologin.com",
                "phone": "(555) 100-0003",
                "city": "Houston",
                "state": "TX",
                "zip_code": "77001",
                "customer_since": "2024-06-01"
            },
            "pets": [
                {"pet_id": "PET-DEMO-005", "customer_id": "DEMO-003", "pet_name": "Charlie", "species": "Dog", "breed": "Labrador", "gender": "Male", "date_of_birth": "2021-11-05", "weight_lbs": 70, "color": "Chocolate", "is_spayed_neutered": True}
            ],
            "policies": [
                {"policy_id": "POL-DEMO-004", "customer_id": "DEMO-003", "pet_id": "PET-DEMO-005", "plan_type": "Basic", "coverage_type": "Accident Only", "monthly_premium": 29.99, "annual_deductible": 750, "reimbursement_percentage": 70, "annual_limit": 5000}
            ]
        }
    }

    results = {"customers": 0, "pets": 0, "policies": 0}

    for demo_id, data in demo_data.items():
        # Add customer
        try:
            insights.add_customer(data["customer"])
            await storage.write_json("customers", data["customer"], demo_id)
            results["customers"] += 1
        except Exception as e:
            print(f"Error adding customer {demo_id}: {e}")

        # Add pets
        for pet in data["pets"]:
            try:
                insights.add_pet(pet)
                results["pets"] += 1
            except Exception as e:
                print(f"Error adding pet {pet['pet_id']}: {e}")

        # Add policies
        for policy in data["policies"]:
            try:
                insights.add_policy(policy)
                results["policies"] += 1
            except Exception as e:
                print(f"Error adding policy {policy['policy_id']}: {e}")

    return {
        "success": True,
        "message": "Demo data seeded successfully",
        "created": results,
        "demo_users": [
            {"id": "DEMO-001", "email": "demo@demologin.com", "name": "Demo User"},
            {"id": "DEMO-002", "email": "demo1@demologin.com", "name": "Demo One"},
            {"id": "DEMO-003", "email": "demo2@demologin.com", "name": "Demo Two"}
        ]
    }


@router.get("/{customer_id}")
async def get_customer(customer_id: str, request: Request):
    """Get customer details."""
    insights = request.app.state.insights
    customers = insights.get_customer_360(customer_id=customer_id, limit=1)

    if customers:
        return {
            "customer": customers[0],
            "message": "Customer found"
        }

    raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
