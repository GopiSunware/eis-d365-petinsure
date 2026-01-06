"""Factor Service - Pet Insurance Rating factors and tables."""
from typing import Dict, Any


class FactorService:
    """Provides rating factors for pet insurance premium calculation."""

    def get_base_rates(self) -> Dict[str, float]:
        """Get base rate by state for pet insurance."""
        return {
            "DEFAULT": 420.00,
            "IL": 420.00,
            "CA": 520.00,
            "TX": 380.00,
            "FL": 480.00,
            "NY": 550.00,
            "PA": 400.00,
            "OH": 360.00,
            "MI": 440.00,
            "GA": 410.00,
            "NC": 390.00,
            "NJ": 510.00,
            "VA": 400.00,
            "WA": 450.00,
            "AZ": 420.00,
            "MA": 490.00,
            "TN": 380.00,
            "IN": 350.00,
            "MO": 370.00,
            "MD": 430.00,
            "WI": 340.00,
            "CO": 460.00,
            "MN": 360.00,
            "SC": 400.00,
            "AL": 390.00,
            "LA": 450.00,
            "KY": 380.00,
            "OR": 440.00,
            "OK": 370.00,
            "CT": 500.00,
            "UT": 380.00,
            "IA": 320.00,
            "NV": 470.00,
            "AR": 360.00,
            "MS": 380.00,
            "KS": 340.00,
            "NM": 400.00,
            "NE": 330.00,
            "WV": 410.00,
            "ID": 350.00,
            "HI": 520.00,
            "NH": 380.00,
            "ME": 370.00,
            "MT": 360.00,
            "RI": 490.00,
            "DE": 450.00,
            "SD": 310.00,
            "ND": 300.00,
            "AK": 480.00,
            "DC": 530.00,
            "VT": 370.00,
            "WY": 350.00,
        }

    def get_species_factors(self) -> Dict[str, Any]:
        """Get species-based rating factors."""
        return {
            "dog": {
                "base_multiplier": 1.00,
                "size_categories": {
                    "small": {"max_weight": 20, "factor": 0.95},
                    "medium": {"max_weight": 50, "factor": 1.00},
                    "large": {"max_weight": 90, "factor": 1.08},
                    "giant": {"max_weight": 999, "factor": 1.15},
                },
            },
            "cat": {
                "base_multiplier": 0.80,
                "size_categories": {
                    "domestic": {"factor": 1.00},
                    "purebred": {"factor": 1.15},
                },
            },
            "bird": {
                "base_multiplier": 0.50,
                "size_categories": {
                    "small": {"factor": 0.90},
                    "large": {"factor": 1.10},
                },
            },
            "rabbit": {
                "base_multiplier": 0.55,
                "size_categories": {
                    "standard": {"factor": 1.00},
                },
            },
            "reptile": {
                "base_multiplier": 0.45,
                "size_categories": {
                    "standard": {"factor": 1.00},
                },
            },
        }

    def get_breed_factors(self) -> Dict[str, Any]:
        """Get breed-specific rating factors for dogs and cats."""
        return {
            # Dogs - High Risk (1.25+)
            "french-bulldog": {
                "breed_id": "french-bulldog",
                "species": "dog",
                "breed_name": "French Bulldog",
                "breed_group": "Non-Sporting",
                "size_category": "small",
                "avg_weight_lbs": 25,
                "avg_lifespan_years": 10,
                "base_rate": 380.00,
                "risk_factor": 1.35,
                "hereditary_conditions": ["boas", "ivdd", "allergies", "hip_dysplasia", "eye_conditions"],
                "age_rating_curve": {"0-1": 0.90, "1-4": 1.00, "4-7": 1.30, "7-10": 1.70, "10+": 2.20},
            },
            "english-bulldog": {
                "breed_id": "english-bulldog",
                "species": "dog",
                "breed_name": "English Bulldog",
                "breed_group": "Non-Sporting",
                "size_category": "medium",
                "avg_weight_lbs": 50,
                "avg_lifespan_years": 8,
                "base_rate": 400.00,
                "risk_factor": 1.45,
                "hereditary_conditions": ["boas", "hip_dysplasia", "cherry_eye", "skin_allergies"],
                "age_rating_curve": {"0-1": 0.95, "1-4": 1.00, "4-7": 1.40, "7+": 2.00},
            },
            "german-shepherd": {
                "breed_id": "german-shepherd",
                "species": "dog",
                "breed_name": "German Shepherd",
                "breed_group": "Herding",
                "size_category": "large",
                "avg_weight_lbs": 75,
                "avg_lifespan_years": 11,
                "base_rate": 420.00,
                "risk_factor": 1.25,
                "hereditary_conditions": ["hip_dysplasia", "elbow_dysplasia", "degenerative_myelopathy", "bloat"],
                "age_rating_curve": {"0-1": 0.85, "1-4": 1.00, "4-7": 1.25, "7-10": 1.60, "10+": 2.10},
            },
            # Dogs - Medium Risk (1.10-1.24)
            "golden-retriever": {
                "breed_id": "golden-retriever",
                "species": "dog",
                "breed_name": "Golden Retriever",
                "breed_group": "Sporting",
                "size_category": "large",
                "avg_weight_lbs": 65,
                "avg_lifespan_years": 11,
                "base_rate": 420.00,
                "risk_factor": 1.15,
                "hereditary_conditions": ["hip_dysplasia", "elbow_dysplasia", "heart_disease", "cancer", "eye_conditions"],
                "age_rating_curve": {"0-1": 0.85, "1-4": 1.00, "4-7": 1.20, "7-10": 1.50, "10+": 2.00},
            },
            "labrador-retriever": {
                "breed_id": "labrador-retriever",
                "species": "dog",
                "breed_name": "Labrador Retriever",
                "breed_group": "Sporting",
                "size_category": "large",
                "avg_weight_lbs": 70,
                "avg_lifespan_years": 12,
                "base_rate": 400.00,
                "risk_factor": 1.10,
                "hereditary_conditions": ["hip_dysplasia", "elbow_dysplasia", "obesity", "eye_conditions"],
                "age_rating_curve": {"0-1": 0.85, "1-4": 1.00, "4-7": 1.15, "7-10": 1.45, "10+": 1.90},
            },
            "rottweiler": {
                "breed_id": "rottweiler",
                "species": "dog",
                "breed_name": "Rottweiler",
                "breed_group": "Working",
                "size_category": "large",
                "avg_weight_lbs": 100,
                "avg_lifespan_years": 10,
                "base_rate": 450.00,
                "risk_factor": 1.20,
                "hereditary_conditions": ["hip_dysplasia", "heart_disease", "cancer", "bloat"],
                "age_rating_curve": {"0-1": 0.88, "1-4": 1.00, "4-7": 1.25, "7-10": 1.65, "10+": 2.10},
            },
            # Dogs - Low Risk (0.90-1.09)
            "beagle": {
                "breed_id": "beagle",
                "species": "dog",
                "breed_name": "Beagle",
                "breed_group": "Hound",
                "size_category": "medium",
                "avg_weight_lbs": 25,
                "avg_lifespan_years": 13,
                "base_rate": 350.00,
                "risk_factor": 0.95,
                "hereditary_conditions": ["epilepsy", "hypothyroidism", "eye_conditions"],
                "age_rating_curve": {"0-1": 0.80, "1-4": 1.00, "4-7": 1.10, "7-10": 1.30, "10+": 1.70},
            },
            "mixed-breed-dog": {
                "breed_id": "mixed-breed-dog",
                "species": "dog",
                "breed_name": "Mixed Breed",
                "breed_group": "Mixed",
                "size_category": "medium",
                "avg_weight_lbs": 45,
                "avg_lifespan_years": 13,
                "base_rate": 360.00,
                "risk_factor": 0.90,
                "hereditary_conditions": [],
                "age_rating_curve": {"0-1": 0.80, "1-4": 1.00, "4-7": 1.08, "7-10": 1.25, "10+": 1.60},
            },
            "poodle": {
                "breed_id": "poodle",
                "species": "dog",
                "breed_name": "Poodle (Standard)",
                "breed_group": "Non-Sporting",
                "size_category": "medium",
                "avg_weight_lbs": 55,
                "avg_lifespan_years": 14,
                "base_rate": 380.00,
                "risk_factor": 1.00,
                "hereditary_conditions": ["hip_dysplasia", "eye_conditions", "bloat"],
                "age_rating_curve": {"0-1": 0.82, "1-4": 1.00, "4-7": 1.10, "7-10": 1.35, "10+": 1.75},
            },
            # Cats
            "maine-coon": {
                "breed_id": "maine-coon",
                "species": "cat",
                "breed_name": "Maine Coon",
                "breed_group": "Purebred",
                "size_category": "large",
                "avg_weight_lbs": 18,
                "avg_lifespan_years": 13,
                "base_rate": 340.00,
                "risk_factor": 1.15,
                "hereditary_conditions": ["hcm", "hip_dysplasia", "sma"],
                "age_rating_curve": {"0-1": 0.85, "1-4": 1.00, "4-7": 1.10, "7-10": 1.30, "10+": 1.60},
            },
            "persian": {
                "breed_id": "persian",
                "species": "cat",
                "breed_name": "Persian",
                "breed_group": "Purebred",
                "size_category": "medium",
                "avg_weight_lbs": 11,
                "avg_lifespan_years": 15,
                "base_rate": 350.00,
                "risk_factor": 1.20,
                "hereditary_conditions": ["pkd", "respiratory_issues", "eye_conditions"],
                "age_rating_curve": {"0-1": 0.85, "1-4": 1.00, "4-7": 1.10, "7-10": 1.25, "10+": 1.55},
            },
            "domestic-shorthair": {
                "breed_id": "domestic-shorthair",
                "species": "cat",
                "breed_name": "Domestic Shorthair",
                "breed_group": "Mixed",
                "size_category": "medium",
                "avg_weight_lbs": 10,
                "avg_lifespan_years": 15,
                "base_rate": 280.00,
                "risk_factor": 0.85,
                "hereditary_conditions": [],
                "age_rating_curve": {"0-1": 0.85, "1-4": 1.00, "4-7": 1.05, "7-10": 1.20, "10-14": 1.45, "14+": 1.75},
            },
            "siamese": {
                "breed_id": "siamese",
                "species": "cat",
                "breed_name": "Siamese",
                "breed_group": "Purebred",
                "size_category": "medium",
                "avg_weight_lbs": 10,
                "avg_lifespan_years": 15,
                "base_rate": 320.00,
                "risk_factor": 1.05,
                "hereditary_conditions": ["asthma", "amyloidosis", "eye_conditions"],
                "age_rating_curve": {"0-1": 0.85, "1-4": 1.00, "4-7": 1.08, "7-10": 1.22, "10+": 1.50},
            },
        }

    def get_age_factors(self) -> Dict[str, Any]:
        """Get age-based rating factors by species."""
        return {
            "dog": {
                "0-1": 0.85,
                "1-4": 1.00,
                "4-7": 1.20,
                "7-10": 1.50,
                "10-12": 2.00,
                "12+": 2.50,
            },
            "cat": {
                "0-1": 0.85,
                "1-4": 1.00,
                "4-7": 1.10,
                "7-10": 1.30,
                "10-14": 1.50,
                "14+": 1.80,
            },
            "bird": {
                "0-2": 0.90,
                "2-10": 1.00,
                "10+": 1.20,
            },
            "rabbit": {
                "0-1": 0.90,
                "1-5": 1.00,
                "5-8": 1.30,
                "8+": 1.60,
            },
            "reptile": {
                "0-5": 1.00,
                "5+": 1.10,
            },
        }

    def get_location_factors(self) -> Dict[str, Any]:
        """Get location-based rating factors."""
        return {
            "DEFAULT": {"state_factor": 1.00, "urban_factor": 1.00},
            "IL": {"state_factor": 1.05, "urban_factor": 1.10},
            "CA": {"state_factor": 1.20, "urban_factor": 1.15},
            "TX": {"state_factor": 0.95, "urban_factor": 1.05},
            "FL": {"state_factor": 1.10, "urban_factor": 1.08},
            "NY": {"state_factor": 1.25, "urban_factor": 1.20},
            "PA": {"state_factor": 1.02, "urban_factor": 1.05},
            "OH": {"state_factor": 0.95, "urban_factor": 1.02},
            "GA": {"state_factor": 1.00, "urban_factor": 1.05},
            "NC": {"state_factor": 0.98, "urban_factor": 1.03},
            "MI": {"state_factor": 1.05, "urban_factor": 1.08},
            "NJ": {"state_factor": 1.18, "urban_factor": 1.15},
            "VA": {"state_factor": 1.00, "urban_factor": 1.05},
            "WA": {"state_factor": 1.10, "urban_factor": 1.10},
            "AZ": {"state_factor": 1.00, "urban_factor": 1.05},
            "MA": {"state_factor": 1.15, "urban_factor": 1.12},
            "CO": {"state_factor": 1.08, "urban_factor": 1.08},
            "OR": {"state_factor": 1.08, "urban_factor": 1.08},
            "NV": {"state_factor": 1.10, "urban_factor": 1.10},
            "HI": {"state_factor": 1.20, "urban_factor": 1.05},
            "DC": {"state_factor": 1.25, "urban_factor": 1.20},
        }

    def get_discounts(self) -> Dict[str, float]:
        """Get available discounts for pet insurance."""
        return {
            "spayed_neutered": 0.05,      # 5% for spayed/neutered pets
            "microchipped": 0.03,          # 3% for microchipped pets
            "multi_pet": 0.10,             # 10% for 2+ pets
            "annual_pay": 0.05,            # 5% for annual payment
            "shelter_rescue": 0.05,        # 5% for shelter/rescue adoptions
            "military_veteran": 0.10,      # 10% for military/veterans
            "loyalty": 0.05,               # 5% for policy renewals
            "wellness_exam": 0.02,         # 2% for annual wellness exam
        }

    def get_plan_factors(self) -> Dict[str, float]:
        """Get plan type multipliers."""
        return {
            "accident_only": 0.40,         # Lowest cost plan
            "accident_illness": 1.00,       # Standard plan (base)
            "comprehensive": 1.35,          # Full coverage plan
        }

    def get_coverage_factors(self) -> Dict[str, Any]:
        """Get coverage option factors."""
        return {
            "annual_limit": {
                5000: 0.85,
                10000: 1.00,
                15000: 1.15,
                0: 1.40,  # Unlimited
            },
            "deductible": {
                100: 1.15,
                250: 1.00,
                500: 0.88,
                750: 0.80,
            },
            "reimbursement_pct": {
                70: 0.85,
                80: 1.00,
                90: 1.20,
            },
        }

    def get_add_on_costs(self) -> Dict[str, float]:
        """Get add-on monthly costs."""
        return {
            "wellness": 15.00,
            "dental": 8.00,
            "behavioral": 5.00,
        }

    def get_waiting_periods(self) -> Dict[str, int]:
        """Get waiting periods in days by condition type."""
        return {
            "accident": 3,
            "illness": 14,
            "orthopedic": 180,
            "hip_dysplasia": 365,
            "cancer": 30,
            "cruciate": 180,
        }
