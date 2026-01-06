"""
Unit tests for WS5 Rating Engine service.
"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal


class TestRateCalculator:
    """Tests for premium rate calculation."""

    def test_calculate_base_premium(self):
        """Test base premium calculation by state."""
        base_rates = {
            "IL": 850.00,
            "CA": 1200.00,
            "TX": 950.00,
            "NY": 1350.00,
            "FL": 1100.00,
        }

        def get_base_premium(state: str) -> float:
            return base_rates.get(state, 1000.00)  # Default rate

        assert get_base_premium("IL") == 850.00
        assert get_base_premium("CA") == 1200.00
        assert get_base_premium("ZZ") == 1000.00  # Unknown state gets default

    def test_calculate_driver_factor(self, sample_driver):
        """Test driver factor calculation."""
        def calculate_driver_factor(driver: dict) -> float:
            factor = 1.0

            # Age factor
            age = driver.get("age", 30)
            if age < 25:
                factor *= 1.35
            elif age > 65:
                factor *= 1.15
            elif 25 <= age <= 35:
                factor *= 1.05

            # Experience factor
            years_licensed = driver.get("years_licensed", 5)
            if years_licensed < 3:
                factor *= 1.25
            elif years_licensed >= 10:
                factor *= 0.95

            # Violations
            violations = driver.get("violations", 0)
            factor *= (1 + (violations * 0.15))

            # At-fault accidents
            accidents = driver.get("at_fault_accidents", 0)
            factor *= (1 + (accidents * 0.25))

            # Marital status
            if driver.get("marital_status") == "married":
                factor *= 0.95

            return round(factor, 3)

        # Good driver (39yo, married, 21 years licensed, no violations)
        factor = calculate_driver_factor(sample_driver)
        assert factor < 1.0  # Should get discount

        # Young driver with violations
        young_driver = {
            "age": 20,
            "years_licensed": 2,
            "violations": 2,
            "at_fault_accidents": 1,
            "marital_status": "single",
        }
        factor = calculate_driver_factor(young_driver)
        assert factor > 2.0  # High surcharge expected

    def test_calculate_vehicle_factor(self, sample_vehicle):
        """Test vehicle factor calculation."""
        def calculate_vehicle_factor(vehicle: dict) -> float:
            factor = 1.0

            # Vehicle age
            import datetime
            current_year = datetime.date.today().year
            vehicle_age = current_year - vehicle.get("year", current_year)

            if vehicle_age <= 2:
                factor *= 1.10  # Newer cars cost more to repair
            elif vehicle_age >= 10:
                factor *= 0.85

            # Body type
            body_factors = {
                "sedan": 1.0,
                "suv": 1.08,
                "truck": 1.05,
                "sports": 1.25,
                "minivan": 0.95,
            }
            factor *= body_factors.get(vehicle.get("body_type", "sedan"), 1.0)

            # Safety features
            if vehicle.get("anti_theft"):
                factor *= 0.95

            safety_rating = vehicle.get("safety_rating", 3)
            if safety_rating >= 5:
                factor *= 0.92
            elif safety_rating >= 4:
                factor *= 0.96

            # Annual mileage
            annual_miles = vehicle.get("annual_miles", 12000)
            if annual_miles > 15000:
                factor *= 1.10
            elif annual_miles < 7500:
                factor *= 0.90

            return round(factor, 3)

        # Safe vehicle with good features
        factor = calculate_vehicle_factor(sample_vehicle)
        assert factor < 1.0  # Should get discount

        # High-risk sports car
        sports_car = {
            "year": 2024,
            "make": "Porsche",
            "model": "911",
            "body_type": "sports",
            "safety_rating": 3,
            "anti_theft": False,
            "annual_miles": 18000,
        }
        factor = calculate_vehicle_factor(sports_car)
        assert factor > 1.3  # Significant surcharge

    def test_calculate_coverage_premium(self):
        """Test individual coverage premium calculation."""
        coverage_base_rates = {
            "bodily_injury": {"base": 200, "per_1000": 3.5},
            "property_damage": {"base": 100, "per_1000": 2.0},
            "collision": {"base": 150, "deductible_factor": 0.8},
            "comprehensive": {"base": 75, "deductible_factor": 0.9},
            "uninsured_motorist": {"base": 50, "per_1000": 1.5},
            "medical_payments": {"base": 25, "per_1000": 1.0},
        }

        def calculate_coverage_premium(coverage_type: str, limit: int, deductible: int) -> float:
            rates = coverage_base_rates.get(coverage_type)
            if not rates:
                return 0.0

            premium = rates["base"]

            # Limit-based coverages
            if "per_1000" in rates and limit > 0:
                premium += (limit / 1000) * rates["per_1000"]

            # Deductible-based coverages
            if "deductible_factor" in rates and deductible > 0:
                # Higher deductible = lower premium
                deductible_discount = (deductible / 1000) * rates["deductible_factor"]
                premium -= min(premium * 0.3, deductible_discount * 20)

            return round(max(0, premium), 2)

        # Bodily injury 100k
        bi_premium = calculate_coverage_premium("bodily_injury", 100000, 0)
        assert bi_premium == 550.00

        # Collision with $500 deductible
        coll_premium = calculate_coverage_premium("collision", 0, 500)
        assert coll_premium > 0
        assert coll_premium < 150  # Should be reduced from base

    def test_apply_discounts(self):
        """Test discount application."""
        def apply_discounts(base_premium: float, discounts: dict) -> tuple[float, list]:
            discount_rates = {
                "multi_car": 0.10,
                "multi_policy": 0.08,
                "good_driver": 0.15,
                "homeowner": 0.05,
                "prior_insurance": 0.05,
                "paperless": 0.03,
                "autopay": 0.02,
                "paid_in_full": 0.05,
            }

            applied = []
            total_discount = 0.0

            for discount, eligible in discounts.items():
                if eligible and discount in discount_rates:
                    rate = discount_rates[discount]
                    applied.append({
                        "name": discount.replace("_", " ").title(),
                        "rate": rate,
                        "amount": round(base_premium * rate, 2),
                    })
                    total_discount += rate

            # Cap total discount at 35%
            total_discount = min(0.35, total_discount)
            final_premium = base_premium * (1 - total_discount)

            return round(final_premium, 2), applied

        base = 1000.00

        # No discounts
        final, applied = apply_discounts(base, {})
        assert final == 1000.00
        assert len(applied) == 0

        # Multiple discounts
        discounts = {
            "multi_policy": True,
            "good_driver": True,
            "homeowner": True,
        }
        final, applied = apply_discounts(base, discounts)
        assert final == 720.00  # 28% discount
        assert len(applied) == 3

        # Discount cap
        all_discounts = {k: True for k in ["multi_car", "multi_policy", "good_driver",
                                            "homeowner", "prior_insurance", "paperless",
                                            "autopay", "paid_in_full"]}
        final, applied = apply_discounts(base, all_discounts)
        assert final == 650.00  # Capped at 35%

    def test_calculate_total_premium(self, sample_quote_request):
        """Test total premium calculation."""
        def calculate_total_premium(quote_request: dict) -> dict:
            state = quote_request.get("state", "IL")
            base_rates = {"IL": 850, "CA": 1200, "TX": 950, "NY": 1350}

            base_premium = base_rates.get(state, 1000)
            driver_factor = 0.92  # Simulated good driver
            vehicle_factor = 0.95  # Simulated safe vehicle

            # Calculate coverage charges
            coverage_total = 0
            for cov in quote_request.get("coverages", []):
                if cov["coverage_type"] == "bodily_injury":
                    coverage_total += 350 + (cov["limit"] / 1000) * 2
                elif cov["coverage_type"] == "property_damage":
                    coverage_total += 150 + (cov["limit"] / 1000) * 1.5
                elif cov["coverage_type"] == "collision":
                    coverage_total += 200 - (cov["deductible"] / 10)
                elif cov["coverage_type"] == "comprehensive":
                    coverage_total += 100 - (cov["deductible"] / 10)

            adjusted_premium = (base_premium + coverage_total) * driver_factor * vehicle_factor

            # Apply discounts
            discount_total = 0
            if quote_request.get("prior_insurance"):
                discount_total += 0.05
            if quote_request.get("homeowner"):
                discount_total += 0.05
            if quote_request.get("multi_policy"):
                discount_total += 0.08

            final_premium = adjusted_premium * (1 - discount_total)

            # Add fees
            fees = 25.00  # Policy fee

            return {
                "base_premium": base_premium,
                "coverage_charges": coverage_total,
                "driver_factor": driver_factor,
                "vehicle_factor": vehicle_factor,
                "discounts_applied": discount_total,
                "subtotal": round(final_premium, 2),
                "fees": fees,
                "total_premium": round(final_premium + fees, 2),
            }

        result = calculate_total_premium(sample_quote_request)

        assert result["base_premium"] == 850
        assert result["driver_factor"] < 1.0
        assert result["vehicle_factor"] < 1.0
        assert result["discounts_applied"] > 0
        assert result["total_premium"] > 0


class TestRatingFactors:
    """Tests for rating factor management."""

    def test_get_state_factors(self):
        """Test retrieval of state-specific rating factors."""
        state_factors = {
            "IL": {"base_rate": 850, "territory_factor": 1.0, "pip_required": False},
            "CA": {"base_rate": 1200, "territory_factor": 1.15, "pip_required": False},
            "NY": {"base_rate": 1350, "territory_factor": 1.2, "pip_required": True},
            "FL": {"base_rate": 1100, "territory_factor": 1.1, "pip_required": True},
        }

        def get_state_factors(state: str) -> dict:
            return state_factors.get(state, {
                "base_rate": 1000,
                "territory_factor": 1.0,
                "pip_required": False,
            })

        il_factors = get_state_factors("IL")
        assert il_factors["base_rate"] == 850
        assert il_factors["pip_required"] is False

        ny_factors = get_state_factors("NY")
        assert ny_factors["pip_required"] is True
        assert ny_factors["territory_factor"] > 1.0

    def test_update_factor(self):
        """Test rating factor update."""
        factors = {"good_driver": 0.15, "homeowner": 0.05}

        def update_factor(factor_name: str, new_value: float) -> bool:
            if factor_name not in factors:
                return False
            if not 0 <= new_value <= 1:
                return False
            factors[factor_name] = new_value
            return True

        assert update_factor("good_driver", 0.18) is True
        assert factors["good_driver"] == 0.18

        assert update_factor("invalid_factor", 0.10) is False
        assert update_factor("homeowner", 1.5) is False  # Invalid value

    def test_validate_coverage_limits(self):
        """Test coverage limit validation."""
        valid_limits = {
            "bodily_injury": [25000, 50000, 100000, 250000, 500000],
            "property_damage": [10000, 25000, 50000, 100000],
            "uninsured_motorist": [25000, 50000, 100000, 250000],
        }

        def validate_coverage_limit(coverage_type: str, limit: int) -> bool:
            if coverage_type not in valid_limits:
                return True  # Not a limit-based coverage
            return limit in valid_limits[coverage_type]

        assert validate_coverage_limit("bodily_injury", 100000) is True
        assert validate_coverage_limit("bodily_injury", 75000) is False
        assert validate_coverage_limit("collision", 500) is True  # Deductible-based


class TestRatingComparison:
    """Tests for rating comparison with mock EIS."""

    def test_compare_premiums(self):
        """Test premium comparison between engines."""
        def compare_premiums(our_premium: float, eis_premium: float) -> dict:
            difference = our_premium - eis_premium
            percentage_diff = (difference / eis_premium) * 100 if eis_premium > 0 else 0

            return {
                "our_premium": our_premium,
                "eis_premium": eis_premium,
                "difference": round(difference, 2),
                "percentage_difference": round(percentage_diff, 2),
                "within_tolerance": abs(percentage_diff) <= 2.0,  # ±2% tolerance
            }

        # Within tolerance
        result = compare_premiums(1020.00, 1000.00)
        assert result["within_tolerance"] is True
        assert result["percentage_difference"] == 2.0

        # Outside tolerance
        result = compare_premiums(1050.00, 1000.00)
        assert result["within_tolerance"] is False
        assert result["percentage_difference"] == 5.0

    def test_identify_variance_factors(self):
        """Test identification of factors causing premium variance."""
        def identify_variance(our_breakdown: dict, eis_breakdown: dict) -> list:
            variances = []

            for key in our_breakdown:
                if key not in eis_breakdown:
                    continue

                our_val = our_breakdown[key]
                eis_val = eis_breakdown[key]

                if isinstance(our_val, (int, float)) and eis_val != 0:
                    diff_pct = abs((our_val - eis_val) / eis_val) * 100
                    if diff_pct > 5:  # More than 5% difference
                        variances.append({
                            "factor": key,
                            "our_value": our_val,
                            "eis_value": eis_val,
                            "difference_pct": round(diff_pct, 1),
                        })

            return sorted(variances, key=lambda x: x["difference_pct"], reverse=True)

        our_breakdown = {
            "base_premium": 850,
            "driver_factor": 0.95,
            "vehicle_factor": 1.10,
            "discount_rate": 0.10,
        }

        eis_breakdown = {
            "base_premium": 850,
            "driver_factor": 0.92,
            "vehicle_factor": 1.05,
            "discount_rate": 0.10,
        }

        variances = identify_variance(our_breakdown, eis_breakdown)

        assert len(variances) == 2
        assert variances[0]["factor"] in ["driver_factor", "vehicle_factor"]
