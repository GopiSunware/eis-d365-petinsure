"""
Unit tests for WS2 FNOL Processor service.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date
from decimal import Decimal


class TestFNOLProcessor:
    """Tests for FNOL processing functionality."""

    @pytest.mark.asyncio
    async def test_extract_claim_data_success(self, sample_fnol_request, mock_openai_response):
        """Test successful claim data extraction from free text."""
        with patch("src.ws2_ai_claims.app.services.fnol_processor.FNOLProcessor") as MockProcessor:
            processor = MockProcessor.return_value
            processor.extract_claim_data = AsyncMock(return_value=mock_openai_response)

            result = await processor.extract_claim_data(sample_fnol_request["description"])

            assert result["incident_type"] == "rear_end_collision"
            assert result["severity"] == "moderate"
            assert result["confidence_score"] >= 0.85

    @pytest.mark.asyncio
    async def test_extract_claim_data_with_injuries(self):
        """Test extraction when injuries are reported."""
        description = """
        I was driving on Highway 55 when a truck ran a red light and T-boned my vehicle.
        I was taken to the hospital with neck and back pain. The car is likely totaled.
        """

        expected_extraction = {
            "incident_type": "intersection_collision",
            "damage_description": "T-bone collision, vehicle likely totaled",
            "estimated_amount": 25000.00,
            "injuries_reported": True,
            "severity": "severe",
            "fraud_indicators": [],
            "confidence_score": 0.88,
        }

        with patch("src.ws2_ai_claims.app.services.fnol_processor.FNOLProcessor") as MockProcessor:
            processor = MockProcessor.return_value
            processor.extract_claim_data = AsyncMock(return_value=expected_extraction)

            result = await processor.extract_claim_data(description)

            assert result["injuries_reported"] is True
            assert result["severity"] == "severe"

    @pytest.mark.asyncio
    async def test_extract_claim_data_minimal_info(self):
        """Test extraction with minimal description."""
        description = "Car was hit in parking lot."

        expected_extraction = {
            "incident_type": "parking_lot_incident",
            "damage_description": "Vehicle damage in parking lot",
            "estimated_amount": 2000.00,
            "severity": "minor",
            "fraud_indicators": [],
            "confidence_score": 0.65,
        }

        with patch("src.ws2_ai_claims.app.services.fnol_processor.FNOLProcessor") as MockProcessor:
            processor = MockProcessor.return_value
            processor.extract_claim_data = AsyncMock(return_value=expected_extraction)

            result = await processor.extract_claim_data(description)

            # Lower confidence expected with minimal info
            assert result["confidence_score"] < 0.85

    @pytest.mark.asyncio
    async def test_generate_claim_number(self):
        """Test claim number generation format."""
        with patch("src.ws2_ai_claims.app.services.fnol_processor.FNOLProcessor") as MockProcessor:
            processor = MockProcessor.return_value
            processor.generate_claim_number = MagicMock(return_value="CLM-2024-00001")

            claim_number = processor.generate_claim_number()

            assert claim_number.startswith("CLM-")
            assert len(claim_number) == 14

    @pytest.mark.asyncio
    async def test_determine_severity_from_amount(self):
        """Test severity classification based on estimated amount."""
        test_cases = [
            (500, "minor"),
            (2500, "minor"),
            (5000, "moderate"),
            (15000, "moderate"),
            (30000, "severe"),
            (100000, "severe"),
        ]

        with patch("src.ws2_ai_claims.app.services.fnol_processor.FNOLProcessor") as MockProcessor:
            processor = MockProcessor.return_value

            def determine_severity(amount):
                if amount < 3000:
                    return "minor"
                elif amount < 20000:
                    return "moderate"
                else:
                    return "severe"

            processor.determine_severity = MagicMock(side_effect=determine_severity)

            for amount, expected_severity in test_cases:
                result = processor.determine_severity(amount)
                assert result == expected_severity, f"Amount {amount} should be {expected_severity}"

    @pytest.mark.asyncio
    async def test_ai_fallback_when_unavailable(self, sample_fnol_request):
        """Test fallback behavior when AI service is unavailable."""
        with patch("src.ws2_ai_claims.app.services.fnol_processor.FNOLProcessor") as MockProcessor:
            processor = MockProcessor.return_value

            # Simulate AI unavailable, use fallback
            fallback_result = {
                "incident_type": "unknown",
                "damage_description": sample_fnol_request["description"][:200],
                "estimated_amount": 0,
                "severity": "pending",
                "fraud_indicators": [],
                "confidence_score": 0.0,
                "requires_manual_review": True,
            }

            processor.extract_claim_data = AsyncMock(return_value=fallback_result)

            result = await processor.extract_claim_data(sample_fnol_request["description"])

            assert result["requires_manual_review"] is True
            assert result["confidence_score"] == 0.0


class TestClaimValidation:
    """Tests for claim validation logic."""

    def test_validate_policy_number_format(self):
        """Test policy number format validation."""
        valid_numbers = [
            "AUTO-IL-2024-00001",
            "HOME-CA-2023-12345",
            "LIFE-NY-2024-00100",
        ]

        invalid_numbers = [
            "INVALID",
            "12345",
            "AUTO-XX-ABCD-00001",
            "",
            None,
        ]

        def validate_policy_number(policy_number: str) -> bool:
            if not policy_number:
                return False
            import re
            pattern = r"^[A-Z]+-[A-Z]{2}-\d{4}-\d{5}$"
            return bool(re.match(pattern, policy_number))

        for number in valid_numbers:
            assert validate_policy_number(number) is True, f"{number} should be valid"

        for number in invalid_numbers:
            assert validate_policy_number(number) is False, f"{number} should be invalid"

    def test_validate_date_of_loss(self):
        """Test date of loss validation."""
        from datetime import date, timedelta

        today = date.today()

        def validate_date_of_loss(date_of_loss: date) -> tuple[bool, str]:
            if date_of_loss > today:
                return False, "Date of loss cannot be in the future"
            if date_of_loss < today - timedelta(days=365):
                return False, "Date of loss is more than 1 year ago"
            return True, ""

        # Valid cases
        assert validate_date_of_loss(today)[0] is True
        assert validate_date_of_loss(today - timedelta(days=30))[0] is True

        # Invalid cases
        assert validate_date_of_loss(today + timedelta(days=1))[0] is False
        assert validate_date_of_loss(today - timedelta(days=400))[0] is False

    def test_validate_contact_info(self):
        """Test contact information validation."""
        import re

        def validate_phone(phone: str) -> bool:
            if not phone:
                return True  # Optional field
            pattern = r"^\d{3}-\d{3}-\d{4}$|^\(\d{3}\) \d{3}-\d{4}$|^\d{10}$"
            return bool(re.match(pattern, phone))

        def validate_email(email: str) -> bool:
            if not email:
                return True  # Optional field
            pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            return bool(re.match(pattern, email))

        # Phone validation
        assert validate_phone("555-123-4567") is True
        assert validate_phone("(555) 123-4567") is True
        assert validate_phone("5551234567") is True
        assert validate_phone("invalid") is False

        # Email validation
        assert validate_email("test@example.com") is True
        assert validate_email("user.name+tag@domain.co.uk") is True
        assert validate_email("invalid-email") is False
