"""Rate Calculator - Pet insurance premium calculation logic."""
import logging
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List

from .factor_service import FactorService

logger = logging.getLogger(__name__)


class RateCalculator:
    """Calculates pet insurance premiums."""

    def __init__(self):
        self.factor_service = FactorService()

    async def calculate(self, request) -> Dict[str, Any]:
        """Calculate premium for pet insurance quote request."""
        quote_id = f"QTE-PET-{datetime.now().strftime('%Y')}-{str(uuid.uuid4())[:5].upper()}"

        # Get base rate for state
        base_rates = self.factor_service.get_base_rates()
        state_rate = base_rates.get(request.state.upper(), base_rates["DEFAULT"])
        base_rate = Decimal(str(state_rate))

        # Calculate pet age
        pet_dob = datetime.strptime(request.pet.date_of_birth, "%Y-%m-%d").date()
        today = date.today()
        pet_age = today.year - pet_dob.year
        if (today.month, today.day) < (pet_dob.month, pet_dob.day):
            pet_age -= 1

        # Get species factor
        species_factors = self.factor_service.get_species_factors()
        species_info = species_factors.get(request.pet.species.lower(), species_factors["dog"])
        species_factor = Decimal(str(species_info.get("base_multiplier", 1.0)))

        # Get breed factor
        breed_factor, size_factor = self._get_breed_and_size_factors(
            request.pet.species,
            request.pet.breed,
            request.pet.weight_lbs,
            species_info,
        )

        # Calculate combined breed factor
        combined_breed_factor = breed_factor * size_factor

        # Get age factor
        age_factor = self._get_age_factor(request.pet.species, pet_age)

        # Get location factor
        location_factors = self.factor_service.get_location_factors()
        loc_info = location_factors.get(request.state.upper(), location_factors["DEFAULT"])
        location_factor = Decimal(str(loc_info["state_factor"])) * Decimal(str(loc_info["urban_factor"]))

        # Calculate base premium with all factors
        base_premium_with_factors = (
            base_rate * species_factor * combined_breed_factor * age_factor * location_factor
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Apply coverage adjustments
        coverage_adjustments = self._calculate_coverage_adjustments(request.coverage)
        plan_factor = coverage_adjustments["plan_factor"]
        limit_factor = coverage_adjustments["limit_factor"]
        deductible_factor = coverage_adjustments["deductible_factor"]
        reimbursement_factor = coverage_adjustments["reimbursement_factor"]

        # Apply all factors multiplicatively (including deductible factor)
        adjusted_premium = (
            base_premium_with_factors * plan_factor * limit_factor * deductible_factor * reimbursement_factor
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Calculate add-on charges
        add_on_charges = self._calculate_add_ons(request.add_ons)
        total_add_ons = sum(Decimal(str(a["annual_cost"])) for a in add_on_charges)

        # Calculate discounts
        discounts = self._calculate_discounts(request, adjusted_premium + total_add_ons)
        total_discounts = sum(Decimal(str(d["amount"])) for d in discounts)

        # Add policy fee
        policy_fee = Decimal("15.00")

        # Calculate total annual premium
        total_annual_premium = (adjusted_premium + total_add_ons - total_discounts + policy_fee).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Calculate monthly payment
        monthly_premium = (total_annual_premium / 12).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Calculate expiration date (1 year from effective)
        effective = datetime.strptime(request.effective_date, "%Y-%m-%d")
        expiration = effective + timedelta(days=365)
        valid_until = effective + timedelta(days=30)

        # Mock EIS comparison
        eis_premium = (total_annual_premium * Decimal("1.012")).quantize(Decimal("0.01"))
        comparison = {
            "eis_premium": eis_premium,
            "difference": total_annual_premium - eis_premium,
            "percentage_diff": round(((total_annual_premium - eis_premium) / eis_premium) * 100, 2),
            "within_tolerance": True,
        }

        return {
            "quote_id": quote_id,
            "pet_age_years": pet_age,
            "base_rate": base_rate,
            "species_factor": species_factor,
            "breed_factor": breed_factor,
            "size_factor": size_factor,
            "combined_breed_factor": combined_breed_factor,
            "age_factor": age_factor,
            "location_factor": location_factor.quantize(Decimal("0.01")),
            "base_premium_with_factors": base_premium_with_factors,
            "coverage_adjustments": {
                "plan_type": request.coverage.plan_type,
                "plan_factor": float(plan_factor),
                "annual_limit_factor": float(limit_factor),
                "deductible_factor": float(deductible_factor),
                "reimbursement_factor": float(reimbursement_factor),
            },
            "adjusted_premium": adjusted_premium,
            "add_on_charges": add_on_charges,
            "discounts": discounts,
            "total_discounts": total_discounts,
            "policy_fee": policy_fee,
            "total_annual_premium": total_annual_premium,
            "monthly_premium": monthly_premium,
            "expiration_date": expiration.strftime("%Y-%m-%d"),
            "valid_until": valid_until.strftime("%Y-%m-%dT23:59:59Z"),
            "comparison": comparison,
        }

    def _get_breed_and_size_factors(
        self,
        species: str,
        breed: str,
        weight_lbs: float | None,
        species_info: Dict,
    ) -> tuple[Decimal, Decimal]:
        """Get breed risk factor and size factor."""
        breed_factors = self.factor_service.get_breed_factors()

        # Normalize breed name to key format
        breed_key = breed.lower().replace(" ", "-")

        # Look up breed-specific factor
        breed_info = breed_factors.get(breed_key)
        if breed_info:
            breed_factor = Decimal(str(breed_info.get("risk_factor", 1.0)))
            size_category = breed_info.get("size_category", "medium")
        else:
            # Default breed factor
            breed_factor = Decimal("1.0")
            size_category = "medium"

        # Calculate size factor based on weight or breed info
        size_factor = Decimal("1.0")
        if species.lower() == "dog":
            size_categories = species_info.get("size_categories", {})
            if weight_lbs:
                # Determine size from weight
                if weight_lbs <= 20:
                    size_factor = Decimal(str(size_categories.get("small", {}).get("factor", 0.95)))
                elif weight_lbs <= 50:
                    size_factor = Decimal(str(size_categories.get("medium", {}).get("factor", 1.00)))
                elif weight_lbs <= 90:
                    size_factor = Decimal(str(size_categories.get("large", {}).get("factor", 1.08)))
                else:
                    size_factor = Decimal(str(size_categories.get("giant", {}).get("factor", 1.15)))
            else:
                # Use breed's typical size category
                if size_category in size_categories:
                    size_factor = Decimal(str(size_categories[size_category].get("factor", 1.0)))

        return breed_factor, size_factor

    def _get_age_factor(self, species: str, age: int) -> Decimal:
        """Get age-based rating factor."""
        age_factors = self.factor_service.get_age_factors()
        species_ages = age_factors.get(species.lower(), age_factors.get("dog", {}))

        # Find the appropriate age band
        for age_range, factor in species_ages.items():
            if "-" in age_range:
                parts = age_range.split("-")
                min_age = int(parts[0])
                max_age = int(parts[1]) if not parts[1].endswith("+") else 999
                if min_age <= age <= max_age:
                    return Decimal(str(factor))
            elif age_range.endswith("+"):
                min_age = int(age_range[:-1])
                if age >= min_age:
                    return Decimal(str(factor))

        # Default factor for adult pets
        return Decimal("1.0")

    def _calculate_coverage_adjustments(self, coverage) -> Dict[str, Decimal]:
        """Calculate coverage-based premium adjustments."""
        coverage_factors = self.factor_service.get_coverage_factors()
        plan_factors = self.factor_service.get_plan_factors()

        # Plan type factor
        plan_factor = Decimal(str(plan_factors.get(coverage.plan_type, 1.0)))

        # Annual limit factor
        limit = int(coverage.annual_limit)
        limit_factor = Decimal(str(coverage_factors["annual_limit"].get(limit, 1.0)))

        # Deductible factor (higher deductible = lower factor = lower premium)
        deductible = int(coverage.deductible)
        deductible_factor = Decimal(str(coverage_factors["deductible"].get(deductible, 1.0)))

        # Reimbursement factor
        reimb_pct = coverage.reimbursement_pct
        reimbursement_factor = Decimal(str(coverage_factors["reimbursement_pct"].get(reimb_pct, 1.0)))

        return {
            "plan_factor": plan_factor,
            "limit_factor": limit_factor,
            "deductible_factor": deductible_factor,
            "reimbursement_factor": reimbursement_factor,
        }

    def _calculate_add_ons(self, add_ons) -> List[Dict[str, Any]]:
        """Calculate add-on charges."""
        add_on_costs = self.factor_service.get_add_on_costs()
        charges = []

        if add_ons.wellness:
            monthly = add_on_costs["wellness"]
            charges.append({
                "type": "wellness",
                "name": "Wellness Add-On",
                "monthly_cost": monthly,
                "annual_cost": monthly * 12,
            })

        if add_ons.dental:
            monthly = add_on_costs["dental"]
            charges.append({
                "type": "dental",
                "name": "Dental Add-On",
                "monthly_cost": monthly,
                "annual_cost": monthly * 12,
            })

        if add_ons.behavioral:
            monthly = add_on_costs["behavioral"]
            charges.append({
                "type": "behavioral",
                "name": "Behavioral Add-On",
                "monthly_cost": monthly,
                "annual_cost": monthly * 12,
            })

        return charges

    def _calculate_discounts(self, request, base_premium: Decimal) -> List[Dict[str, Any]]:
        """Calculate applicable discounts."""
        discounts = []
        discount_rates = self.factor_service.get_discounts()
        total_discount_rate = Decimal("0")
        max_discount = Decimal("0.30")  # 30% cap

        # Spayed/neutered discount
        if request.pet.spayed_neutered:
            rate = Decimal(str(discount_rates["spayed_neutered"]))
            total_discount_rate += rate
            amount = (base_premium * rate).quantize(Decimal("0.01"))
            discounts.append({
                "name": "Spayed/Neutered",
                "rate": rate,
                "amount": amount,
            })

        # Microchipped discount
        if request.pet.microchipped:
            rate = Decimal(str(discount_rates["microchipped"]))
            total_discount_rate += rate
            amount = (base_premium * rate).quantize(Decimal("0.01"))
            discounts.append({
                "name": "Microchipped",
                "rate": rate,
                "amount": amount,
            })

        # Multi-pet discount
        if request.discounts.multi_pet:
            rate = Decimal(str(discount_rates["multi_pet"]))
            total_discount_rate += rate
            amount = (base_premium * rate).quantize(Decimal("0.01"))
            discounts.append({
                "name": "Multi-Pet",
                "rate": rate,
                "amount": amount,
            })

        # Annual pay discount
        if request.discounts.annual_pay:
            rate = Decimal(str(discount_rates["annual_pay"]))
            total_discount_rate += rate
            amount = (base_premium * rate).quantize(Decimal("0.01"))
            discounts.append({
                "name": "Annual Payment",
                "rate": rate,
                "amount": amount,
            })

        # Shelter/rescue discount
        if request.discounts.shelter_rescue:
            rate = Decimal(str(discount_rates["shelter_rescue"]))
            total_discount_rate += rate
            amount = (base_premium * rate).quantize(Decimal("0.01"))
            discounts.append({
                "name": "Shelter/Rescue",
                "rate": rate,
                "amount": amount,
            })

        # Military/veteran discount
        if request.discounts.military_veteran:
            rate = Decimal(str(discount_rates["military_veteran"]))
            total_discount_rate += rate
            amount = (base_premium * rate).quantize(Decimal("0.01"))
            discounts.append({
                "name": "Military/Veteran",
                "rate": rate,
                "amount": amount,
            })

        # Apply discount cap if exceeded
        if total_discount_rate > max_discount:
            cap_ratio = max_discount / total_discount_rate
            for d in discounts:
                d["amount"] = (d["amount"] * cap_ratio).quantize(Decimal("0.01"))

        return discounts
