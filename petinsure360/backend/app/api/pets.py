"""
PetInsure360 - Pets API
Endpoints for pet registration and management
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from app.models.schemas import PetCreate, PetResponse

router = APIRouter()

@router.post("/", response_model=PetResponse)
async def create_pet(pet: PetCreate, request: Request):
    """
    Register a new pet for a customer.

    Writes pet data to Azure Data Lake Storage for ETL processing.
    """
    # Generate pet ID
    pet_id = f"PET-{uuid.uuid4().hex[:8].upper()}"

    # Prepare data for storage (convert enum values to strings)
    pet_dict = pet.model_dump()
    pet_data = {
        "pet_id": pet_id,
        "customer_id": pet_dict.get("customer_id"),
        "pet_name": pet_dict.get("pet_name"),
        "species": pet.species.value if hasattr(pet.species, 'value') else str(pet.species),
        "breed": pet_dict.get("breed"),
        "date_of_birth": pet_dict.get("date_of_birth"),
        "gender": pet.gender.value if pet.gender and hasattr(pet.gender, 'value') else str(pet.gender) if pet.gender else None,
        "weight_lbs": pet_dict.get("weight_lbs"),
        "color": pet_dict.get("color"),
        "microchip_id": pet_dict.get("microchip_id"),
        "is_neutered": pet_dict.get("is_neutered"),
        "pre_existing_conditions": pet_dict.get("pre_existing_conditions"),
        "adoption_date": None,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    # Write to ADLS
    storage = request.app.state.storage
    await storage.write_json("pets", pet_data, pet_id)

    # Add to in-memory insights data for real-time BI display
    insights = request.app.state.insights
    insights.add_pet(pet_data)

    # Emit WebSocket event
    sio = request.app.state.sio
    await sio.emit('pet_added', {
        'pet_id': pet_id,
        'customer_id': pet.customer_id,
        'pet_name': pet.pet_name,
        'species': pet.species.value,
        'timestamp': datetime.utcnow().isoformat()
    })

    return PetResponse(
        pet_id=pet_id,
        customer_id=pet.customer_id,
        pet_name=pet.pet_name,
        species=pet.species.value,
        breed=pet.breed,
        created_at=datetime.utcnow(),
        message=f"Pet {pet.pet_name} ({pet_id}) registered successfully"
    )

@router.get("/{pet_id}")
async def get_pet(pet_id: str, request: Request):
    """Get pet details."""
    return {
        "pet_id": pet_id,
        "message": "Query pet from Gold layer (not implemented in demo)"
    }

@router.get("/customer/{customer_id}")
async def get_customer_pets(customer_id: str, request: Request):
    """Get all pets for a customer."""
    insights = request.app.state.insights
    pets_list = insights.get_customer_pets(customer_id)

    return {
        "customer_id": customer_id,
        "pets": pets_list,
        "count": len(pets_list)
    }
