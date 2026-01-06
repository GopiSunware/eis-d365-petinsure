"""Rating engine configuration models."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict

from pydantic import BaseModel, Field


class BaseRates(BaseModel):
    """Base premium rates by species."""
    dog: Decimal = Field(default=Decimal("45.00"))
    cat: Decimal = Field(default=Decimal("28.00"))
    exotic: Decimal = Field(default=Decimal("65.00"))
    bird: Decimal = Field(default=Decimal("35.00"))
    rabbit: Decimal = Field(default=Decimal("30.00"))


class BreedFactor(BaseModel):
    """Breed-specific rating factor."""
    breed_name: str
    species: str  # dog, cat, exotic
    multiplier: float = Field(ge=0.5, le=5.0)
    risk_notes: Optional[str] = None
    common_conditions: List[str] = Field(default_factory=list)


class BreedMultipliers(BaseModel):
    """Breed multipliers by species."""
    dogs: List[BreedFactor] = Field(default_factory=lambda: [
        BreedFactor(breed_name="French Bulldog", species="dog", multiplier=1.8,
                    risk_notes="Respiratory, skin issues",
                    common_conditions=["Brachycephalic syndrome", "Skin allergies"]),
        BreedFactor(breed_name="English Bulldog", species="dog", multiplier=2.0,
                    risk_notes="Hip, respiratory issues",
                    common_conditions=["Hip dysplasia", "Cherry eye"]),
        BreedFactor(breed_name="German Shepherd", species="dog", multiplier=1.4,
                    risk_notes="Hip dysplasia prone",
                    common_conditions=["Hip dysplasia", "Degenerative myelopathy"]),
        BreedFactor(breed_name="Golden Retriever", species="dog", multiplier=1.3,
                    risk_notes="Cancer, hip issues",
                    common_conditions=["Cancer", "Hip dysplasia"]),
        BreedFactor(breed_name="Labrador Retriever", species="dog", multiplier=1.2,
                    risk_notes="Hip, obesity prone",
                    common_conditions=["Hip dysplasia", "Obesity"]),
        BreedFactor(breed_name="Poodle (Standard)", species="dog", multiplier=1.15,
                    risk_notes="Eye, skin conditions",
                    common_conditions=["Progressive retinal atrophy", "Addison's disease"]),
        BreedFactor(breed_name="Beagle", species="dog", multiplier=1.1,
                    risk_notes="Epilepsy prone",
                    common_conditions=["Epilepsy", "Hypothyroidism"]),
        BreedFactor(breed_name="Mixed Breed", species="dog", multiplier=1.0,
                    risk_notes="Baseline risk"),
        BreedFactor(breed_name="Chihuahua", species="dog", multiplier=1.1,
                    risk_notes="Dental, patella issues",
                    common_conditions=["Luxating patella", "Dental disease"]),
        BreedFactor(breed_name="Pug", species="dog", multiplier=1.7,
                    risk_notes="Respiratory, eye issues",
                    common_conditions=["Brachycephalic syndrome", "Eye problems"]),
    ])
    cats: List[BreedFactor] = Field(default_factory=lambda: [
        BreedFactor(breed_name="Persian", species="cat", multiplier=1.3,
                    risk_notes="Respiratory, kidney issues",
                    common_conditions=["PKD", "Respiratory issues"]),
        BreedFactor(breed_name="Siamese", species="cat", multiplier=1.2,
                    risk_notes="Dental, respiratory",
                    common_conditions=["Dental disease", "Asthma"]),
        BreedFactor(breed_name="Maine Coon", species="cat", multiplier=1.25,
                    risk_notes="Heart, hip issues",
                    common_conditions=["HCM", "Hip dysplasia"]),
        BreedFactor(breed_name="Domestic Shorthair", species="cat", multiplier=1.0,
                    risk_notes="Baseline risk"),
        BreedFactor(breed_name="Bengal", species="cat", multiplier=1.15,
                    risk_notes="Heart, eye issues",
                    common_conditions=["HCM", "PRA"]),
        BreedFactor(breed_name="Ragdoll", species="cat", multiplier=1.2,
                    risk_notes="Heart issues",
                    common_conditions=["HCM", "Bladder stones"]),
    ])
    exotic: List[BreedFactor] = Field(default_factory=list)


class AgeFactors(BaseModel):
    """Age-based rating factors."""
    ranges: Dict[str, float] = Field(default_factory=lambda: {
        "0-1": 1.0,
        "1-4": 1.0,
        "4-7": 1.3,
        "7-10": 1.6,
        "10-12": 2.0,
        "12+": 2.5,
    })
    max_enrollment_age_dogs: int = 14
    max_enrollment_age_cats: int = 16
    max_enrollment_age_exotic: int = 10


class GeographicFactors(BaseModel):
    """Geographic rating factors based on vet costs."""
    regions: Dict[str, float] = Field(default_factory=lambda: {
        "new_york": 1.4,
        "california": 1.35,
        "massachusetts": 1.3,
        "washington": 1.25,
        "colorado": 1.2,
        "texas": 1.1,
        "florida": 1.15,
        "midwest": 1.0,
        "south": 0.95,
        "default": 1.0,
    })


class Discounts(BaseModel):
    """Available discounts."""
    multi_pet: float = Field(default=0.10, ge=0, le=0.5)  # 10% off each additional pet
    annual_pay: float = Field(default=0.05, ge=0, le=0.2)  # 5% for annual payment
    military: float = Field(default=0.10, ge=0, le=0.2)
    shelter_adoption: float = Field(default=0.05, ge=0, le=0.2)
    microchip: float = Field(default=0.02, ge=0, le=0.1)
    spayed_neutered: float = Field(default=0.03, ge=0, le=0.1)
    loyalty: Dict[str, float] = Field(default_factory=lambda: {
        "1_year": 0.02,
        "2_years": 0.04,
        "3_years": 0.06,
        "5_years": 0.10,
    })


class RatingFactorsConfig(BaseModel):
    """Complete rating factors configuration."""
    id: str = "rating_config"
    config_type: str = "rating_config"  # Partition key
    version: int = 1

    base_rates: BaseRates = Field(default_factory=BaseRates)
    breed_multipliers: BreedMultipliers = Field(default_factory=BreedMultipliers)
    age_factors: AgeFactors = Field(default_factory=AgeFactors)
    geographic_factors: GeographicFactors = Field(default_factory=GeographicFactors)
    discounts: Discounts = Field(default_factory=Discounts)

    # Deductible options and their premium adjustments
    deductible_adjustments: Dict[str, float] = Field(default_factory=lambda: {
        "0": 1.25,      # No deductible = 25% higher premium
        "100": 1.1,     # $100 deductible = 10% higher
        "250": 1.0,     # $250 = baseline
        "500": 0.9,     # $500 = 10% lower
        "750": 0.85,    # $750 = 15% lower
        "1000": 0.8,    # $1000 = 20% lower
    })

    # Reimbursement level adjustments
    reimbursement_adjustments: Dict[str, float] = Field(default_factory=lambda: {
        "70": 0.85,     # 70% reimbursement = 15% lower premium
        "80": 1.0,      # 80% = baseline
        "90": 1.2,      # 90% = 20% higher
        "100": 1.5,     # 100% = 50% higher
    })

    # Metadata
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None


class RatingFactorsUpdate(BaseModel):
    """Request to update rating factors."""
    base_rates: Optional[BaseRates] = None
    breed_multipliers: Optional[BreedMultipliers] = None
    age_factors: Optional[AgeFactors] = None
    geographic_factors: Optional[GeographicFactors] = None
    discounts: Optional[Discounts] = None
    deductible_adjustments: Optional[Dict[str, float]] = None
    reimbursement_adjustments: Optional[Dict[str, float]] = None


class PremiumCalculation(BaseModel):
    """Premium calculation request/response."""
    species: str
    breed: str
    age_years: int
    region: str
    plan: str
    deductible: int
    reimbursement_percent: int

    # Calculated values (response)
    base_rate: Optional[Decimal] = None
    breed_factor: Optional[float] = None
    age_factor: Optional[float] = None
    geographic_factor: Optional[float] = None
    plan_factor: Optional[float] = None
    deductible_adjustment: Optional[float] = None
    reimbursement_adjustment: Optional[float] = None
    discounts_applied: Dict[str, float] = Field(default_factory=dict)
    monthly_premium: Optional[Decimal] = None
    annual_premium: Optional[Decimal] = None
