"""Customer and Pet domain models for pet insurance."""
from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class CustomerType(str, Enum):
    """Type of customer."""
    INDIVIDUAL = "individual"
    BUSINESS = "business"
    TRUST = "trust"


class Species(str, Enum):
    """Pet species."""
    DOG = "dog"
    CAT = "cat"
    BIRD = "bird"
    RABBIT = "rabbit"
    REPTILE = "reptile"


class Gender(str, Enum):
    """Pet gender."""
    MALE = "male"
    FEMALE = "female"


class Address(BaseModel):
    """Physical address."""
    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str = "USA"


class Pet(BaseModel):
    """Pet information for insurance."""
    id: Optional[str] = None
    pet_id: Optional[str] = None
    name: str = Field(..., max_length=100)
    species: Species = Species.DOG
    breed: str = Field(..., max_length=100)
    breed_group: Optional[str] = None
    date_of_birth: date
    gender: Gender = Gender.MALE
    microchip_id: Optional[str] = Field(default=None, max_length=20)
    spayed_neutered: bool = False
    weight_lbs: Optional[float] = Field(default=None, ge=0)
    color: Optional[str] = None
    policy_id: Optional[str] = None
    owner_id: Optional[str] = None
    pre_existing_conditions: List[str] = Field(default_factory=list)
    vaccination_status: str = "current"
    last_vet_visit: Optional[date] = None
    external_pet_id: Optional[str] = None

    model_config = {"use_enum_values": True}

    @property
    def age_years(self) -> int:
        """Calculate pet age in years."""
        today = date.today()
        age = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
        return age

    def to_dataverse_record(self) -> dict:
        """Convert to Dataverse entity format."""
        species_map = {"dog": 100000000, "cat": 100000001, "bird": 100000002, "rabbit": 100000003, "reptile": 100000004}
        gender_map = {"male": 100000000, "female": 100000001}

        record = {
            "eis_name": self.name,
            "eis_species": species_map.get(self.species, 100000000),
            "eis_breed": self.breed,
            "eis_dateofbirth": self.date_of_birth.isoformat(),
            "eis_gender": gender_map.get(self.gender, 100000000),
            "eis_spayedneutered": self.spayed_neutered,
        }

        if self.microchip_id:
            record["eis_microchipid"] = self.microchip_id
        if self.weight_lbs:
            record["eis_weightlbs"] = self.weight_lbs
        if self.color:
            record["eis_color"] = self.color
        if self.owner_id:
            record["eis_OwnerId@odata.bind"] = f"/eis_petowners({self.owner_id})"
        if self.external_pet_id:
            record["eis_externalpetid"] = self.external_pet_id

        return record


class Customer(BaseModel):
    """Pet owner / customer."""
    id: Optional[str] = None
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=20)
    date_of_birth: Optional[date] = None
    customer_type: CustomerType = CustomerType.INDIVIDUAL
    address: Optional[Address] = None
    pets: List[Pet] = Field(default_factory=list)
    external_customer_id: Optional[str] = None

    model_config = {"use_enum_values": True}

    @property
    def full_name(self) -> str:
        """Get full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def pets_count(self) -> int:
        """Get number of pets."""
        return len(self.pets)

    def to_dataverse_record(self) -> dict:
        """Convert to Dataverse entity format."""
        customer_type_map = {
            "individual": 100000000,
            "business": 100000001,
            "trust": 100000002,
        }

        record = {
            "eis_firstname": self.first_name,
            "eis_lastname": self.last_name,
            "eis_fullname": self.full_name,
            "eis_customertype": customer_type_map.get(self.customer_type, 100000000),
        }

        if self.email:
            record["eis_email"] = self.email

        if self.phone:
            record["eis_phone"] = self.phone

        if self.date_of_birth:
            record["eis_dateofbirth"] = self.date_of_birth.isoformat()

        if self.address:
            record["eis_addressline1"] = self.address.line1
            record["eis_city"] = self.address.city
            record["eis_stateorprovince"] = self.address.state
            record["eis_postalcode"] = self.address.postal_code

        if self.external_customer_id:
            record["eis_externalcustomerid"] = self.external_customer_id

        return record

    @classmethod
    def from_dataverse_record(cls, record: dict) -> "Customer":
        """Create from Dataverse entity."""
        customer_type_map = {
            100000000: "individual",
            100000001: "business",
            100000002: "trust",
        }

        address = None
        if record.get("eis_addressline1"):
            address = Address(
                line1=record["eis_addressline1"],
                city=record.get("eis_city", ""),
                state=record.get("eis_stateorprovince", ""),
                postal_code=record.get("eis_postalcode", ""),
            )

        dob = None
        if record.get("eis_dateofbirth"):
            dob = date.fromisoformat(record["eis_dateofbirth"][:10])

        return cls(
            id=record.get("eis_insuredpartyid"),
            first_name=record["eis_firstname"],
            last_name=record["eis_lastname"],
            email=record.get("eis_email"),
            phone=record.get("eis_phone"),
            date_of_birth=dob,
            customer_type=customer_type_map.get(record.get("eis_customertype"), "individual"),
            address=address,
            external_customer_id=record.get("eis_externalcustomerid"),
        )
