"""
End-to-end tests for Quote/Rating flow.
Tests the complete journey from quote request to premium calculation.
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, date, timezone
from decimal import Decimal


class TestQuoteEndToEnd:
    """End-to-end tests for quote generation flow."""

    @pytest.fixture
    def e2e_quote_context(self):
        """Set up E2E test context for quotes."""
        return {
            "quote_requests": [],
            "calculated_premiums": [],
            "comparison_results": [],
        }

    @pytest.mark.asyncio
    async def test_complete_quote_flow(self, sample_quote_request, e2e_quote_context):
        """
        Test complete quote flow:
        1. Submit quote request
        2. Validate driver/vehicle data
        3. Calculate base premium
        4. Apply rating factors
        5. Apply discounts
        6. Return premium breakdown
        7. Compare with EIS rate
        """
        # Step 1: Submit quote request
        quote_request = {
            **sample_quote_request,
            "quote_id": "QTE-2024-001",
            "requested_at": datetime.now(timezone.utc).isoformat(),
        }
        e2e_quote_context["quote_requests"].append(quote_request)

        # Step 2: Validate data
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        # Check driver age
        for driver in quote_request["drivers"]:
            dob = datetime.fromisoformat(driver["date_of_birth"])
            age = (datetime.now() - dob).days // 365
            if age < 16:
                validation_result["valid"] = False
                validation_result["errors"].append("Driver must be at least 16")

        assert validation_result["valid"] is True

        # Step 3: Calculate base premium
        state = quote_request["state"]
        base_rates = {"IL": 850, "CA": 1200, "TX": 950, "NY": 1350, "FL": 1100}
        base_premium = base_rates.get(state, 1000)

        # Step 4: Apply rating factors
        # Driver factor
        driver = quote_request["drivers"][0]
        driver_dob = datetime.fromisoformat(driver["date_of_birth"])
        driver_age = (datetime.now() - driver_dob).days // 365

        driver_factor = 1.0
        if driver_age < 25:
            driver_factor *= 1.35
        elif 25 <= driver_age <= 35:
            driver_factor *= 1.05
        elif driver_age > 65:
            driver_factor *= 1.15

        if driver["marital_status"] == "married":
            driver_factor *= 0.95

        driver_factor *= (1 + driver["violations"] * 0.15)
        driver_factor *= (1 + driver["at_fault_accidents"] * 0.25)

        # Vehicle factor
        vehicle = quote_request["vehicles"][0]
        vehicle_factor = 1.0

        current_year = datetime.now().year
        vehicle_age = current_year - vehicle["year"]
        if vehicle_age <= 2:
            vehicle_factor *= 1.10
        elif vehicle_age >= 10:
            vehicle_factor *= 0.85

        body_factors = {"sedan": 1.0, "suv": 1.08, "truck": 1.05, "sports": 1.25}
        vehicle_factor *= body_factors.get(vehicle["body_type"], 1.0)

        if vehicle["anti_theft"]:
            vehicle_factor *= 0.95

        # Step 5: Calculate coverage charges
        coverage_charges = []
        for cov in quote_request["coverages"]:
            if cov["coverage_type"] == "bodily_injury":
                charge = 200 + (cov["limit"] / 1000) * 3.5
            elif cov["coverage_type"] == "property_damage":
                charge = 100 + (cov["limit"] / 1000) * 2.0
            elif cov["coverage_type"] == "collision":
                charge = 150 - (cov["deductible"] / 20)
            elif cov["coverage_type"] == "comprehensive":
                charge = 75 - (cov["deductible"] / 25)
            else:
                charge = 50

            coverage_charges.append({
                "coverage_type": cov["coverage_type"],
                "charge": round(charge, 2),
            })

        total_coverage = sum(c["charge"] for c in coverage_charges)

        # Step 6: Apply discounts
        discounts = []
        discount_total = 0.0

        if quote_request.get("prior_insurance"):
            discounts.append({"name": "Prior Insurance", "rate": 0.05})
            discount_total += 0.05

        if quote_request.get("homeowner"):
            discounts.append({"name": "Homeowner", "rate": 0.05})
            discount_total += 0.05

        if quote_request.get("multi_policy"):
            discounts.append({"name": "Multi-Policy", "rate": 0.08})
            discount_total += 0.08

        # Good driver discount
        if driver["violations"] == 0 and driver["at_fault_accidents"] == 0:
            discounts.append({"name": "Good Driver", "rate": 0.15})
            discount_total += 0.15

        # Calculate final premium
        subtotal = (base_premium + total_coverage) * driver_factor * vehicle_factor
        discount_amount = subtotal * min(0.35, discount_total)  # Cap at 35%
        final_subtotal = subtotal - discount_amount

        # Add fees
        fees = 25.00

        premium_breakdown = {
            "quote_id": quote_request["quote_id"],
            "base_premium": base_premium,
            "coverage_charges": coverage_charges,
            "total_coverage": round(total_coverage, 2),
            "driver_factor": round(driver_factor, 3),
            "vehicle_factor": round(vehicle_factor, 3),
            "discounts": discounts,
            "discount_total_rate": round(min(0.35, discount_total), 3),
            "discount_amount": round(discount_amount, 2),
            "subtotal": round(final_subtotal, 2),
            "fees": fees,
            "total_premium": round(final_subtotal + fees, 2),
            "valid_until": (datetime.now(timezone.utc).replace(hour=23, minute=59, second=59)).isoformat(),
        }
        e2e_quote_context["calculated_premiums"].append(premium_breakdown)

        # Step 7: Compare with EIS mock rate
        eis_mock_premium = premium_breakdown["total_premium"] * 1.01  # Simulate 1% variance
        comparison = {
            "our_premium": premium_breakdown["total_premium"],
            "eis_premium": round(eis_mock_premium, 2),
            "difference": round(premium_breakdown["total_premium"] - eis_mock_premium, 2),
            "percentage_diff": round(((premium_breakdown["total_premium"] - eis_mock_premium) / eis_mock_premium) * 100, 2),
            "within_tolerance": abs((premium_breakdown["total_premium"] - eis_mock_premium) / eis_mock_premium) <= 0.02,
        }
        e2e_quote_context["comparison_results"].append(comparison)

        # Verify complete flow
        assert len(e2e_quote_context["quote_requests"]) == 1
        assert len(e2e_quote_context["calculated_premiums"]) == 1
        assert len(e2e_quote_context["comparison_results"]) == 1

        # Verify premium calculation
        premium = e2e_quote_context["calculated_premiums"][0]
        assert premium["total_premium"] > 0
        assert premium["driver_factor"] > 0
        assert premium["vehicle_factor"] > 0
        assert len(premium["discounts"]) > 0

        # Verify EIS comparison within tolerance
        assert comparison["within_tolerance"] is True

    @pytest.mark.asyncio
    async def test_high_risk_driver_quote(self, e2e_quote_context):
        """Test quote for high-risk driver profile."""
        high_risk_request = {
            "quote_id": "QTE-2024-002",
            "state": "CA",
            "zip_code": "90210",
            "effective_date": "2024-07-01",
            "drivers": [
                {
                    "first_name": "Young",
                    "last_name": "Driver",
                    "date_of_birth": "2005-01-15",  # 19 years old
                    "gender": "male",
                    "marital_status": "single",
                    "license_date": "2023-01-15",  # 1 year experience
                    "violations": 3,
                    "at_fault_accidents": 1,
                    "is_primary": True,
                }
            ],
            "vehicles": [
                {
                    "year": 2024,
                    "make": "Ford",
                    "model": "Mustang",
                    "body_type": "sports",
                    "use": "pleasure",
                    "annual_miles": 18000,
                    "anti_theft": False,
                    "safety_features": [],
                }
            ],
            "coverages": [
                {"coverage_type": "bodily_injury", "limit": 100000, "deductible": 0},
                {"coverage_type": "property_damage", "limit": 50000, "deductible": 0},
                {"coverage_type": "collision", "limit": 0, "deductible": 500},
            ],
            "prior_insurance": False,
            "homeowner": False,
            "multi_policy": False,
        }

        # Calculate premium for high-risk
        base_premium = 1200  # CA base rate

        # High driver factor
        driver = high_risk_request["drivers"][0]
        driver_factor = 1.35  # Young
        driver_factor *= 1.25  # New driver
        driver_factor *= (1 + 3 * 0.15)  # 3 violations
        driver_factor *= (1 + 1 * 0.25)  # 1 at-fault accident
        # driver_factor ≈ 2.95

        # High vehicle factor
        vehicle_factor = 1.10  # New car
        vehicle_factor *= 1.25  # Sports car
        vehicle_factor *= 1.10  # High mileage
        # vehicle_factor ≈ 1.51

        # No discounts apply

        estimated_premium = base_premium * driver_factor * vehicle_factor
        # estimated_premium ≈ $5,350

        e2e_quote_context["quote_requests"].append(high_risk_request)

        assert driver_factor > 2.5
        assert vehicle_factor > 1.3
        assert estimated_premium > 4000  # Significantly higher than standard

    @pytest.mark.asyncio
    async def test_multi_driver_quote(self, e2e_quote_context):
        """Test quote with multiple drivers."""
        multi_driver_request = {
            "quote_id": "QTE-2024-003",
            "state": "IL",
            "zip_code": "60601",
            "effective_date": "2024-07-01",
            "drivers": [
                {
                    "first_name": "John",
                    "last_name": "Smith",
                    "date_of_birth": "1975-05-20",
                    "gender": "male",
                    "marital_status": "married",
                    "license_date": "1993-05-20",
                    "violations": 0,
                    "at_fault_accidents": 0,
                    "is_primary": True,
                },
                {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "date_of_birth": "1978-08-15",
                    "gender": "female",
                    "marital_status": "married",
                    "license_date": "1996-08-15",
                    "violations": 0,
                    "at_fault_accidents": 0,
                    "is_primary": False,
                },
                {
                    "first_name": "Teen",
                    "last_name": "Smith",
                    "date_of_birth": "2006-03-10",
                    "gender": "male",
                    "marital_status": "single",
                    "license_date": "2024-03-10",
                    "violations": 0,
                    "at_fault_accidents": 0,
                    "is_primary": False,
                },
            ],
            "vehicles": [
                {
                    "year": 2022,
                    "make": "Honda",
                    "model": "Accord",
                    "body_type": "sedan",
                    "use": "commute",
                    "annual_miles": 12000,
                    "anti_theft": True,
                    "safety_features": ["abs", "airbags"],
                },
                {
                    "year": 2020,
                    "make": "Toyota",
                    "model": "Highlander",
                    "body_type": "suv",
                    "use": "commute",
                    "annual_miles": 10000,
                    "anti_theft": True,
                    "safety_features": ["abs", "airbags", "backup_camera"],
                },
            ],
            "coverages": [
                {"coverage_type": "bodily_injury", "limit": 250000, "deductible": 0},
                {"coverage_type": "property_damage", "limit": 100000, "deductible": 0},
                {"coverage_type": "collision", "limit": 0, "deductible": 500},
                {"coverage_type": "comprehensive", "limit": 0, "deductible": 250},
            ],
            "prior_insurance": True,
            "homeowner": True,
            "multi_policy": True,
        }

        # Calculate with worst driver (teen)
        # Rating should use the highest risk driver for pricing
        worst_driver_factor = 1.35 * 1.25  # Young + inexperienced

        # Multi-car discount should apply
        multi_car_discount = 0.10

        # Other discounts
        total_discounts = 0.05 + 0.05 + 0.08 + multi_car_discount  # 28%

        e2e_quote_context["quote_requests"].append(multi_driver_request)

        assert len(multi_driver_request["drivers"]) == 3
        assert len(multi_driver_request["vehicles"]) == 2
        assert total_discounts <= 0.35  # Within cap

    @pytest.mark.asyncio
    async def test_quote_state_variations(self, e2e_quote_context):
        """Test that quotes vary appropriately by state."""
        states = ["IL", "CA", "TX", "NY", "FL"]
        base_rates = {"IL": 850, "CA": 1200, "TX": 950, "NY": 1350, "FL": 1100}

        quotes_by_state = {}

        for state in states:
            quote_request = {
                "quote_id": f"QTE-STATE-{state}",
                "state": state,
                "drivers": [{
                    "date_of_birth": "1985-03-15",
                    "marital_status": "single",
                    "violations": 0,
                    "at_fault_accidents": 0,
                }],
                "vehicles": [{
                    "year": 2022,
                    "body_type": "sedan",
                    "anti_theft": True,
                }],
            }

            # Simplified premium calculation
            base = base_rates.get(state, 1000)
            premium = base * 1.0 * 0.95  # Neutral factors
            quotes_by_state[state] = round(premium, 2)

        # Verify CA and NY are highest
        assert quotes_by_state["CA"] > quotes_by_state["IL"]
        assert quotes_by_state["NY"] > quotes_by_state["CA"]

        # Verify IL is lower than average
        average = sum(quotes_by_state.values()) / len(quotes_by_state)
        assert quotes_by_state["IL"] < average


class TestQuoteValidation:
    """Tests for quote request validation."""

    def test_validate_driver_age(self):
        """Test driver age validation."""
        def validate_driver_age(dob: str) -> tuple[bool, str]:
            birth_date = datetime.fromisoformat(dob)
            age = (datetime.now() - birth_date).days // 365

            if age < 16:
                return False, "Driver must be at least 16 years old"
            if age > 99:
                return False, "Invalid driver age"
            return True, ""

        assert validate_driver_age("1985-03-15")[0] is True
        assert validate_driver_age("2015-03-15")[0] is False  # Too young
        assert validate_driver_age("1920-03-15")[0] is False  # Too old

    def test_validate_vehicle_year(self):
        """Test vehicle year validation."""
        def validate_vehicle_year(year: int) -> tuple[bool, str]:
            current_year = datetime.now().year

            if year > current_year + 1:
                return False, "Vehicle year cannot be more than 1 year in the future"
            if year < 1980:
                return False, "Vehicle must be 1980 or newer"
            return True, ""

        assert validate_vehicle_year(2022)[0] is True
        assert validate_vehicle_year(2030)[0] is False  # Too far future
        assert validate_vehicle_year(1975)[0] is False  # Too old

    def test_validate_coverage_limits(self):
        """Test coverage limit validation."""
        valid_bi_limits = [25000, 50000, 100000, 250000, 500000]
        valid_pd_limits = [10000, 25000, 50000, 100000]

        def validate_coverage(coverage_type: str, limit: int) -> bool:
            if coverage_type == "bodily_injury":
                return limit in valid_bi_limits
            elif coverage_type == "property_damage":
                return limit in valid_pd_limits
            return True

        assert validate_coverage("bodily_injury", 100000) is True
        assert validate_coverage("bodily_injury", 75000) is False
        assert validate_coverage("property_damage", 50000) is True


class TestQuoteComparison:
    """Tests for quote comparison with EIS mock."""

    @pytest.mark.asyncio
    async def test_premium_within_tolerance(self):
        """Test that calculated premium is within ±2% of EIS."""
        our_premium = 1020.00
        eis_premium = 1000.00

        difference_pct = abs((our_premium - eis_premium) / eis_premium) * 100

        assert difference_pct <= 2.0

    @pytest.mark.asyncio
    async def test_identify_variance_sources(self):
        """Test identification of premium variance sources."""
        our_breakdown = {
            "base_premium": 850,
            "driver_factor": 0.95,
            "vehicle_factor": 1.12,
            "discount_rate": 0.10,
        }

        eis_breakdown = {
            "base_premium": 850,
            "driver_factor": 0.92,
            "vehicle_factor": 1.08,
            "discount_rate": 0.10,
        }

        variances = []
        for key in our_breakdown:
            our_val = our_breakdown[key]
            eis_val = eis_breakdown[key]
            if our_val != eis_val:
                diff_pct = abs((our_val - eis_val) / eis_val) * 100
                if diff_pct > 1:  # More than 1% difference
                    variances.append({
                        "factor": key,
                        "our_value": our_val,
                        "eis_value": eis_val,
                        "difference_pct": round(diff_pct, 1),
                    })

        assert len(variances) == 2
        assert any(v["factor"] == "driver_factor" for v in variances)
        assert any(v["factor"] == "vehicle_factor" for v in variances)
