"""
Data loader for the Unified Claims Data API.
Loads JSON data files and provides in-memory access.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from functools import lru_cache

DATA_DIR = Path(__file__).parent.parent / "data"


class DataStore:
    """In-memory data store loaded from JSON files."""

    def __init__(self):
        self._customers: List[Dict] = []
        self._pets: List[Dict] = []
        self._policies: List[Dict] = []
        self._providers: List[Dict] = []
        self._claims: List[Dict] = []
        self._medical_codes: List[Dict] = []
        self._payments: List[Dict] = []
        self._fraud_patterns: Dict = {}

        # Index maps for fast lookups
        self._customer_by_id: Dict[str, Dict] = {}
        self._pet_by_id: Dict[str, Dict] = {}
        self._policy_by_id: Dict[str, Dict] = {}
        self._provider_by_id: Dict[str, Dict] = {}
        self._claim_by_id: Dict[str, Dict] = {}
        self._code_by_code: Dict[str, Dict] = {}

        self._loaded = False

    def load(self):
        """Load all data from JSON files."""
        if self._loaded:
            return

        print("Loading data from JSON files...")

        # Load customers
        customers_file = DATA_DIR / "customers.json"
        if customers_file.exists():
            with open(customers_file) as f:
                self._customers = json.load(f)
                self._customer_by_id = {c["customer_id"]: c for c in self._customers}
            print(f"  Loaded {len(self._customers)} customers")

        # Load pets
        pets_file = DATA_DIR / "pets.json"
        if pets_file.exists():
            with open(pets_file) as f:
                self._pets = json.load(f)
                self._pet_by_id = {p["pet_id"]: p for p in self._pets}
            print(f"  Loaded {len(self._pets)} pets")

        # Load policies
        policies_file = DATA_DIR / "policies.json"
        if policies_file.exists():
            with open(policies_file) as f:
                self._policies = json.load(f)
                self._policy_by_id = {p["policy_id"]: p for p in self._policies}
            print(f"  Loaded {len(self._policies)} policies")

        # Load providers
        providers_file = DATA_DIR / "providers.json"
        if providers_file.exists():
            with open(providers_file) as f:
                self._providers = json.load(f)
                self._provider_by_id = {p["provider_id"]: p for p in self._providers}
            print(f"  Loaded {len(self._providers)} providers")

        # Load claims
        claims_file = DATA_DIR / "claims_history.json"
        if claims_file.exists():
            with open(claims_file) as f:
                self._claims = json.load(f)
                self._claim_by_id = {c["claim_id"]: c for c in self._claims}
            print(f"  Loaded {len(self._claims)} claims")

        # Load medical codes
        codes_file = DATA_DIR / "medical_codes.json"
        if codes_file.exists():
            with open(codes_file) as f:
                self._medical_codes = json.load(f)
                self._code_by_code = {c["code"]: c for c in self._medical_codes}
            print(f"  Loaded {len(self._medical_codes)} medical codes")

        # Load payments
        payments_file = DATA_DIR / "payments.json"
        if payments_file.exists():
            with open(payments_file) as f:
                self._payments = json.load(f)
            print(f"  Loaded {len(self._payments)} payments")

        # Load fraud patterns
        fraud_file = DATA_DIR / "fraud_patterns.json"
        if fraud_file.exists():
            with open(fraud_file) as f:
                self._fraud_patterns = json.load(f)
            print(f"  Loaded fraud patterns config")

        self._loaded = True
        print("Data loading complete!")

    # Customer methods
    def get_customers(self) -> List[Dict]:
        return self._customers

    def get_customer(self, customer_id: str) -> Optional[Dict]:
        return self._customer_by_id.get(customer_id)

    def get_customers_by_segment(self, segment: str) -> List[Dict]:
        return [c for c in self._customers if c.get("segment") == segment]

    # Pet methods
    def get_pets(self) -> List[Dict]:
        return self._pets

    def get_pet(self, pet_id: str) -> Optional[Dict]:
        return self._pet_by_id.get(pet_id)

    def get_pets_by_customer(self, customer_id: str) -> List[Dict]:
        return [p for p in self._pets if p.get("customer_id") == customer_id]

    def get_pets_by_species(self, species: str) -> List[Dict]:
        return [p for p in self._pets if p.get("species", "").lower() == species.lower()]

    # Policy methods
    def get_policies(self) -> List[Dict]:
        return self._policies

    def get_policy(self, policy_id: str) -> Optional[Dict]:
        return self._policy_by_id.get(policy_id)

    def get_policies_by_customer(self, customer_id: str) -> List[Dict]:
        return [p for p in self._policies if p.get("customer_id") == customer_id]

    def get_policies_by_pet(self, pet_id: str) -> List[Dict]:
        return [p for p in self._policies if p.get("pet_id") == pet_id]

    def get_active_policies(self) -> List[Dict]:
        return [p for p in self._policies if p.get("status") == "active"]

    # Provider methods
    def get_providers(self) -> List[Dict]:
        return self._providers

    def get_provider(self, provider_id: str) -> Optional[Dict]:
        return self._provider_by_id.get(provider_id)

    def get_in_network_providers(self) -> List[Dict]:
        return [p for p in self._providers if p.get("is_in_network")]

    def search_providers(self, name: str) -> List[Dict]:
        name_lower = name.lower()
        return [p for p in self._providers if name_lower in p.get("name", "").lower()]

    # Claim methods
    def get_claims(self) -> List[Dict]:
        return self._claims

    def get_claim(self, claim_id: str) -> Optional[Dict]:
        return self._claim_by_id.get(claim_id)

    def get_claims_by_customer(self, customer_id: str) -> List[Dict]:
        return [c for c in self._claims if c.get("customer_id") == customer_id]

    def get_claims_by_pet(self, pet_id: str) -> List[Dict]:
        return [c for c in self._claims if c.get("pet_id") == pet_id]

    def get_claims_by_policy(self, policy_id: str) -> List[Dict]:
        return [c for c in self._claims if c.get("policy_id") == policy_id]

    def get_claims_by_provider(self, provider_id: str) -> List[Dict]:
        return [c for c in self._claims if c.get("provider_id") == provider_id]

    def get_claims_by_status(self, status: str) -> List[Dict]:
        return [c for c in self._claims if c.get("status") == status]

    def get_fraud_claims(self) -> List[Dict]:
        return [c for c in self._claims if c.get("fraud_pattern")]

    # Medical code methods
    def get_medical_codes(self) -> List[Dict]:
        return self._medical_codes

    def get_medical_code(self, code: str) -> Optional[Dict]:
        return self._code_by_code.get(code)

    def search_medical_codes(self, term: str) -> List[Dict]:
        term_lower = term.lower()
        return [
            c for c in self._medical_codes
            if term_lower in c.get("code", "").lower() or term_lower in c.get("description", "").lower()
        ]

    # Payment methods
    def get_payments(self) -> List[Dict]:
        return self._payments

    def get_payments_by_customer(self, customer_id: str) -> List[Dict]:
        return [p for p in self._payments if p.get("customer_id") == customer_id]

    def get_payments_by_claim(self, claim_id: str) -> List[Dict]:
        return [p for p in self._payments if p.get("claim_id") == claim_id]

    # Fraud patterns
    def get_fraud_patterns(self) -> Dict:
        return self._fraud_patterns


# Singleton instance
_data_store: Optional[DataStore] = None


def get_data_store() -> DataStore:
    """Get the singleton data store instance."""
    global _data_store
    if _data_store is None:
        _data_store = DataStore()
        _data_store.load()
    return _data_store
