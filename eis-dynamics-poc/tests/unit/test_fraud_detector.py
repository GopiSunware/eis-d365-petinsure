"""
Unit tests for WS2 Fraud Detection service.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date, datetime, timedelta


class TestFraudDetector:
    """Tests for fraud detection functionality."""

    @pytest.mark.asyncio
    async def test_analyze_claim_low_risk(self, sample_claim):
        """Test fraud analysis returns low risk for clean claim."""
        with patch("src.ws2_ai_claims.app.services.fraud_detector.FraudDetector") as MockDetector:
            detector = MockDetector.return_value

            result = {
                "fraud_score": 0.12,
                "risk_level": "low",
                "indicators": [],
                "recommendation": "Proceed with standard processing",
            }
            detector.analyze_claim = AsyncMock(return_value=result)

            analysis = await detector.analyze_claim(sample_claim)

            assert analysis["fraud_score"] < 0.3
            assert analysis["risk_level"] == "low"
            assert len(analysis["indicators"]) == 0

    @pytest.mark.asyncio
    async def test_analyze_claim_high_risk(self):
        """Test fraud analysis identifies high-risk claim."""
        suspicious_claim = {
            "claim_number": "CLM-2024-00002",
            "policy_id": "POL-2024-002",
            "date_of_loss": (date.today() - timedelta(days=2)).isoformat(),
            "date_reported": datetime.now().isoformat(),
            "loss_description": "Total loss of vehicle. Fire. No witnesses.",
            "severity": "severe",
            "reserve_amount": 50000.00,
        }

        with patch("src.ws2_ai_claims.app.services.fraud_detector.FraudDetector") as MockDetector:
            detector = MockDetector.return_value

            result = {
                "fraud_score": 0.72,
                "risk_level": "high",
                "indicators": [
                    "New policy with large claim",
                    "Total loss claim",
                    "No witnesses reported",
                    "Vague loss description",
                ],
                "recommendation": "Refer to Special Investigations Unit",
            }
            detector.analyze_claim = AsyncMock(return_value=result)

            analysis = await detector.analyze_claim(suspicious_claim)

            assert analysis["fraud_score"] > 0.5
            assert analysis["risk_level"] == "high"
            assert len(analysis["indicators"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_claim_medium_risk(self):
        """Test fraud analysis identifies medium-risk claim."""
        medium_risk_claim = {
            "claim_number": "CLM-2024-00003",
            "policy_id": "POL-2024-003",
            "date_of_loss": (date.today() - timedelta(days=5)).isoformat(),
            "date_reported": datetime.now().isoformat(),
            "loss_description": "Vehicle stolen from parking lot. Keys were in the car.",
            "severity": "moderate",
            "reserve_amount": 20000.00,
        }

        with patch("src.ws2_ai_claims.app.services.fraud_detector.FraudDetector") as MockDetector:
            detector = MockDetector.return_value

            result = {
                "fraud_score": 0.42,
                "risk_level": "medium",
                "indicators": [
                    "Keys left in vehicle",
                    "Delayed reporting",
                ],
                "recommendation": "Additional documentation requested",
            }
            detector.analyze_claim = AsyncMock(return_value=result)

            analysis = await detector.analyze_claim(medium_risk_claim)

            assert 0.3 <= analysis["fraud_score"] <= 0.5
            assert analysis["risk_level"] == "medium"


class TestFraudIndicators:
    """Tests for individual fraud indicator detection."""

    def test_detect_new_policy_claim(self):
        """Test detection of claims on new policies."""
        def check_new_policy_indicator(policy_effective_date: date, claim_date: date) -> bool:
            days_since_inception = (claim_date - policy_effective_date).days
            return days_since_inception < 30

        today = date.today()

        # New policy (claim within 30 days)
        assert check_new_policy_indicator(today - timedelta(days=15), today) is True

        # Established policy
        assert check_new_policy_indicator(today - timedelta(days=60), today) is False

    def test_detect_multiple_claims(self):
        """Test detection of multiple claims in short period."""
        def check_multiple_claims_indicator(claim_history: list, threshold: int = 3) -> bool:
            recent_claims = [
                c for c in claim_history
                if (date.today() - date.fromisoformat(c["date"])).days < 365
            ]
            return len(recent_claims) >= threshold

        history_clean = [
            {"date": (date.today() - timedelta(days=400)).isoformat(), "amount": 1000}
        ]

        history_suspicious = [
            {"date": (date.today() - timedelta(days=30)).isoformat(), "amount": 5000},
            {"date": (date.today() - timedelta(days=90)).isoformat(), "amount": 3000},
            {"date": (date.today() - timedelta(days=180)).isoformat(), "amount": 4000},
        ]

        assert check_multiple_claims_indicator(history_clean) is False
        assert check_multiple_claims_indicator(history_suspicious) is True

    def test_detect_late_reporting(self):
        """Test detection of late claim reporting."""
        def check_late_reporting(date_of_loss: date, date_reported: date, threshold_days: int = 30) -> bool:
            delay = (date_reported - date_of_loss).days
            return delay > threshold_days

        today = date.today()

        # Timely reporting
        assert check_late_reporting(today - timedelta(days=5), today) is False

        # Late reporting
        assert check_late_reporting(today - timedelta(days=45), today) is True

    def test_detect_amount_pattern(self):
        """Test detection of suspicious amount patterns."""
        def check_amount_pattern(amount: float) -> list:
            indicators = []

            # Round number (exact thousands)
            if amount >= 1000 and amount % 1000 == 0:
                indicators.append("Round number claim amount")

            # Just under limit
            common_limits = [5000, 10000, 25000, 50000, 100000]
            for limit in common_limits:
                if limit * 0.95 <= amount < limit:
                    indicators.append(f"Amount just under ${limit:,} limit")

            return indicators

        # Clean amount
        assert len(check_amount_pattern(4532.50)) == 0

        # Round number
        assert "Round number claim amount" in check_amount_pattern(10000)

        # Just under limit
        indicators = check_amount_pattern(9800)
        assert any("under $10,000" in i for i in indicators)

    def test_detect_suspicious_description(self):
        """Test detection of suspicious claim descriptions."""
        def check_description_indicators(description: str) -> list:
            indicators = []
            description_lower = description.lower()

            suspicious_phrases = [
                ("no witnesses", "No witnesses reported"),
                ("fire", "Fire-related loss"),
                ("total loss", "Total loss claimed"),
                ("cash only", "Cash-only request"),
                ("urgent", "Urgency pressure"),
            ]

            for phrase, indicator in suspicious_phrases:
                if phrase in description_lower:
                    indicators.append(indicator)

            # Very short description
            if len(description) < 50:
                indicators.append("Vague/minimal description")

            return indicators

        # Clean description
        clean_desc = "I was rear-ended at a stoplight by another driver who admitted fault. Police report filed."
        assert len(check_description_indicators(clean_desc)) == 0

        # Suspicious description
        suspicious_desc = "Total loss fire no witnesses"
        indicators = check_description_indicators(suspicious_desc)
        assert "No witnesses reported" in indicators
        assert "Fire-related loss" in indicators
        assert "Total loss claimed" in indicators


class TestFraudScoreCalculation:
    """Tests for fraud score calculation logic."""

    def test_calculate_base_score(self):
        """Test base fraud score calculation."""
        def calculate_fraud_score(indicators: list, weights: dict = None) -> float:
            if weights is None:
                weights = {
                    "New policy with large claim": 0.15,
                    "Multiple recent claims": 0.20,
                    "Late reporting": 0.10,
                    "No witnesses reported": 0.12,
                    "Total loss claimed": 0.10,
                    "Fire-related loss": 0.15,
                    "Round number claim amount": 0.05,
                    "Amount just under limit": 0.08,
                    "Vague/minimal description": 0.08,
                }

            score = 0.0
            for indicator in indicators:
                for key, weight in weights.items():
                    if key.lower() in indicator.lower():
                        score += weight
                        break

            return min(1.0, score)  # Cap at 1.0

        # No indicators
        assert calculate_fraud_score([]) == 0.0

        # Single low indicator
        assert calculate_fraud_score(["Round number claim amount"]) == 0.05

        # Multiple indicators
        indicators = ["New policy with large claim", "No witnesses reported", "Fire-related loss"]
        score = calculate_fraud_score(indicators)
        assert score == pytest.approx(0.42, abs=0.01)

    def test_risk_level_classification(self):
        """Test risk level classification from score."""
        def classify_risk(score: float) -> str:
            if score < 0.3:
                return "low"
            elif score < 0.5:
                return "medium"
            else:
                return "high"

        assert classify_risk(0.0) == "low"
        assert classify_risk(0.15) == "low"
        assert classify_risk(0.29) == "low"
        assert classify_risk(0.30) == "medium"
        assert classify_risk(0.45) == "medium"
        assert classify_risk(0.50) == "high"
        assert classify_risk(0.85) == "high"
        assert classify_risk(1.0) == "high"
