"""
PetInsure360 - Pet Recommendations API
Provides pet care recommendations, insurance suggestions, and breed information
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import random

router = APIRouter()


# =============================================================================
# MODELS
# =============================================================================

class PetInfo(BaseModel):
    species: str  # Dog or Cat
    breed: str
    traits: Optional[List[str]] = None


class InsurancePlan(BaseModel):
    name: str
    price: str
    coverage: str
    recommended: bool
    reason: str


class CareItem(BaseModel):
    item: str
    frequency: str


class CostItem(BaseModel):
    item: str
    cost: str


class BreedInfo(BaseModel):
    breed: str
    species: str
    traits: List[str]
    lifespan: str
    size: str


class RecommendationsResponse(BaseModel):
    insurance_plans: List[InsurancePlan]
    health_tips: List[str]
    care_items: List[CareItem]
    cost_items: List[CostItem]
    breed_info: BreedInfo


class ImageAnalysisResponse(BaseModel):
    species: str
    breed: str
    confidence: float
    traits: List[str]


# =============================================================================
# DATA
# =============================================================================

DOG_BREEDS = [
    "Golden Retriever", "German Shepherd", "Labrador Retriever", "French Bulldog",
    "Beagle", "Poodle", "Siberian Husky", "Bulldog", "Rottweiler", "Yorkshire Terrier",
    "Boxer", "Dachshund", "Shih Tzu", "Great Dane", "Chihuahua", "Mixed Breed"
]

CAT_BREEDS = [
    "Persian", "Maine Coon", "Siamese", "British Shorthair", "Bengal",
    "Ragdoll", "Abyssinian", "Scottish Fold", "Sphynx", "Russian Blue",
    "Domestic Shorthair", "Domestic Longhair", "Tabby", "Mixed Breed"
]

DOG_TRAITS = [
    "Loyal", "Friendly", "Active", "Playful", "Intelligent", "Protective",
    "Gentle", "Energetic", "Affectionate", "Social", "Trainable", "Alert"
]

CAT_TRAITS = [
    "Independent", "Curious", "Affectionate", "Playful", "Calm", "Quiet",
    "Intelligent", "Graceful", "Social", "Loyal", "Adventurous", "Gentle"
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_dog_recommendations(breed: str) -> RecommendationsResponse:
    """Generate recommendations for dogs"""

    # Determine size category based on breed
    large_breeds = ["German Shepherd", "Golden Retriever", "Labrador Retriever",
                    "Siberian Husky", "Rottweiler", "Great Dane", "Boxer"]
    is_large = breed in large_breeds

    insurance_plans = [
        InsurancePlan(
            name="Premium Plan",
            price="$79.99/mo",
            coverage="$20,000",
            recommended=is_large,
            reason="Best for active breeds, covers hip dysplasia" if is_large else "Comprehensive coverage"
        ),
        InsurancePlan(
            name="Standard Plan",
            price="$49.99/mo",
            coverage="$10,000",
            recommended=not is_large,
            reason="Good balance of coverage and cost"
        ),
        InsurancePlan(
            name="Basic Plan",
            price="$29.99/mo",
            coverage="$5,000",
            recommended=False,
            reason="Essential accident and illness coverage"
        )
    ]

    health_tips = [
        "Regular exercise - at least 30-60 minutes daily",
        "Annual vet checkups and vaccinations are essential",
        "Dental cleaning recommended every 6-12 months",
        "Keep up with heartworm and flea prevention",
        "Monitor weight to prevent obesity-related issues",
        "Provide mental stimulation with toys and training"
    ]

    if is_large:
        health_tips.append("Watch for hip dysplasia in larger breeds")
        health_tips.append("Consider joint supplements as they age")

    care_items = [
        CareItem(item="Grooming", frequency="Weekly brushing, bath monthly"),
        CareItem(item="Exercise", frequency="30-60 min daily walks"),
        CareItem(item="Training", frequency="Ongoing socialization recommended"),
        CareItem(item="Vet visits", frequency="Annual checkup + vaccinations"),
        CareItem(item="Nail trimming", frequency="Every 2-4 weeks")
    ]

    cost_items = [
        CostItem(item="Food", cost="$50-100"),
        CostItem(item="Treats & Toys", cost="$20-40"),
        CostItem(item="Grooming", cost="$30-80"),
        CostItem(item="Vet (averaged)", cost="$50-100"),
        CostItem(item="Insurance", cost="$30-80")
    ]

    breed_info = BreedInfo(
        breed=breed,
        species="Dog",
        traits=random.sample(DOG_TRAITS, 4),
        lifespan="10-14 years" if is_large else "12-16 years",
        size="Large" if is_large else "Small to Medium"
    )

    return RecommendationsResponse(
        insurance_plans=insurance_plans,
        health_tips=health_tips,
        care_items=care_items,
        cost_items=cost_items,
        breed_info=breed_info
    )


def generate_cat_recommendations(breed: str) -> RecommendationsResponse:
    """Generate recommendations for cats"""

    # Determine if breed needs extra care
    high_maintenance = ["Persian", "Maine Coon", "Ragdoll", "Sphynx"]
    needs_extra_care = breed in high_maintenance

    insurance_plans = [
        InsurancePlan(
            name="Standard Plan",
            price="$49.99/mo",
            coverage="$10,000",
            recommended=needs_extra_care,
            reason="Comprehensive coverage for indoor cats"
        ),
        InsurancePlan(
            name="Basic Plan",
            price="$29.99/mo",
            coverage="$5,000",
            recommended=not needs_extra_care,
            reason="Essential coverage for healthy cats"
        ),
        InsurancePlan(
            name="Wellness Plan",
            price="$39.99/mo",
            coverage="$7,500",
            recommended=False,
            reason="Includes routine care and vaccines"
        )
    ]

    health_tips = [
        "Keep indoors for safety and longer lifespan",
        "Annual vet checkups and vaccinations",
        "Dental care - watch for gum disease",
        "Monitor weight - obesity is common in cats",
        "Provide scratching posts for claw health",
        "Ensure fresh water is always available"
    ]

    if needs_extra_care:
        health_tips.append("Regular grooming to prevent matting")
        health_tips.append("Monitor for breed-specific health issues")

    care_items = [
        CareItem(item="Grooming", frequency="Brush 2-3 times weekly"),
        CareItem(item="Litter box", frequency="Clean daily, full change weekly"),
        CareItem(item="Play time", frequency="15-30 min interactive play daily"),
        CareItem(item="Vet visits", frequency="Annual checkup + vaccinations"),
        CareItem(item="Nail trimming", frequency="Every 2-3 weeks")
    ]

    cost_items = [
        CostItem(item="Food", cost="$30-60"),
        CostItem(item="Litter", cost="$15-30"),
        CostItem(item="Treats & Toys", cost="$10-25"),
        CostItem(item="Vet (averaged)", cost="$40-80"),
        CostItem(item="Insurance", cost="$20-50")
    ]

    breed_info = BreedInfo(
        breed=breed,
        species="Cat",
        traits=random.sample(CAT_TRAITS, 4),
        lifespan="12-18 years",
        size="Medium" if breed in ["Maine Coon", "Ragdoll"] else "Small to Medium"
    )

    return RecommendationsResponse(
        insurance_plans=insurance_plans,
        health_tips=health_tips,
        care_items=care_items,
        cost_items=cost_items,
        breed_info=breed_info
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/breeds/{species}")
async def get_breeds(species: str):
    """Get list of breeds by species"""
    species_lower = species.lower()

    if species_lower == "dog":
        return {"species": "Dog", "breeds": DOG_BREEDS}
    elif species_lower == "cat":
        return {"species": "Cat", "breeds": CAT_BREEDS}
    else:
        raise HTTPException(status_code=400, detail="Species must be 'dog' or 'cat'")


@router.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_pet_image(file: UploadFile = File(...)):
    """
    Analyze uploaded pet image to detect species and breed.
    In production, this would use Azure Computer Vision or similar AI service.
    """

    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Read file (in production, send to AI service)
    contents = await file.read()

    # Simulated AI detection (random for demo)
    species = random.choice(["Dog", "Cat"])
    breeds = DOG_BREEDS if species == "Dog" else CAT_BREEDS
    traits = DOG_TRAITS if species == "Dog" else CAT_TRAITS

    return ImageAnalysisResponse(
        species=species,
        breed=random.choice(breeds),
        confidence=random.uniform(0.80, 0.99),
        traits=random.sample(traits, 3)
    )


@router.post("/get", response_model=RecommendationsResponse)
async def get_recommendations(pet_info: PetInfo):
    """Get personalized recommendations for a pet"""

    species_lower = pet_info.species.lower()

    if species_lower == "dog":
        return generate_dog_recommendations(pet_info.breed)
    elif species_lower == "cat":
        return generate_cat_recommendations(pet_info.breed)
    else:
        raise HTTPException(status_code=400, detail="Species must be 'dog' or 'cat'")


@router.get("/sample-pets")
async def get_sample_pets():
    """Get sample pet images for selection"""

    sample_dogs = [
        {"id": 1, "name": "Golden Retriever", "species": "Dog", "breed": "Golden Retriever",
         "image": "https://images.unsplash.com/photo-1552053831-71594a27632d?w=300&h=300&fit=crop",
         "traits": ["Friendly", "Active", "Family-oriented"]},
        {"id": 2, "name": "German Shepherd", "species": "Dog", "breed": "German Shepherd",
         "image": "https://images.unsplash.com/photo-1589941013453-ec89f33b5e95?w=300&h=300&fit=crop",
         "traits": ["Loyal", "Protective", "Intelligent"]},
        {"id": 3, "name": "Labrador", "species": "Dog", "breed": "Labrador Retriever",
         "image": "https://images.unsplash.com/photo-1579213838058-824f2f024be6?w=300&h=300&fit=crop",
         "traits": ["Playful", "Gentle", "Outgoing"]},
        {"id": 4, "name": "French Bulldog", "species": "Dog", "breed": "French Bulldog",
         "image": "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=300&h=300&fit=crop",
         "traits": ["Adaptable", "Playful", "Smart"]},
        {"id": 5, "name": "Husky", "species": "Dog", "breed": "Siberian Husky",
         "image": "https://images.unsplash.com/photo-1605568427561-40dd23c2acea?w=300&h=300&fit=crop",
         "traits": ["Energetic", "Outgoing", "Mischievous"]},
    ]

    sample_cats = [
        {"id": 6, "name": "Persian Cat", "species": "Cat", "breed": "Persian",
         "image": "https://images.unsplash.com/photo-1574158622682-e40e69881006?w=300&h=300&fit=crop",
         "traits": ["Calm", "Affectionate", "Quiet"]},
        {"id": 7, "name": "Maine Coon", "species": "Cat", "breed": "Maine Coon",
         "image": "https://images.unsplash.com/photo-1615497001839-b0a0eac3274c?w=300&h=300&fit=crop",
         "traits": ["Gentle Giant", "Playful", "Social"]},
        {"id": 8, "name": "Siamese Cat", "species": "Cat", "breed": "Siamese",
         "image": "https://images.unsplash.com/photo-1513360371669-4adf3dd7dff8?w=300&h=300&fit=crop",
         "traits": ["Vocal", "Affectionate", "Social"]},
        {"id": 9, "name": "British Shorthair", "species": "Cat", "breed": "British Shorthair",
         "image": "https://images.unsplash.com/photo-1596854407944-bf87f6fdd49e?w=300&h=300&fit=crop",
         "traits": ["Easy-going", "Loyal", "Independent"]},
        {"id": 10, "name": "Bengal Cat", "species": "Cat", "breed": "Bengal",
         "image": "https://images.unsplash.com/photo-1606567595334-d39972c85dfd?w=300&h=300&fit=crop",
         "traits": ["Energetic", "Intelligent", "Athletic"]},
    ]

    return {
        "dogs": sample_dogs,
        "cats": sample_cats,
        "total": len(sample_dogs) + len(sample_cats)
    }
