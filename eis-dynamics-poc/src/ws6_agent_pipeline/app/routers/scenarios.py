"""
Scenarios API router for demo claim scenarios.
"""

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])

# Load scenarios data
SCENARIOS_FILE = Path(__file__).parent.parent.parent / "data" / "claim_scenarios.json"


def load_scenarios() -> list[dict[str, Any]]:
    """Load scenarios from JSON file."""
    try:
        with open(SCENARIOS_FILE, "r") as f:
            data = json.load(f)
            return data.get("scenarios", [])
    except FileNotFoundError:
        logger.warning(f"Scenarios file not found: {SCENARIOS_FILE}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing scenarios file: {e}")
        return []


@router.get("/")
async def get_scenarios():
    """
    Get all available claim scenarios.

    Returns 20 pre-built demo scenarios with realistic medical data
    covering emergencies, surgeries, chronic conditions, and wellness.
    """
    scenarios = load_scenarios()
    return {
        "scenarios": scenarios,
        "count": len(scenarios),
    }


@router.get("/{scenario_id}")
async def get_scenario(scenario_id: str):
    """
    Get a specific scenario by ID.
    """
    scenarios = load_scenarios()

    for scenario in scenarios:
        if scenario.get("id") == scenario_id:
            return scenario

    raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")


@router.get("/complexity/{level}")
async def get_scenarios_by_complexity(level: str):
    """
    Get scenarios filtered by complexity level.

    Complexity is determined by claim amount:
    - simple: < $1000
    - medium: $1000 - $5000
    - complex: > $5000
    """
    scenarios = load_scenarios()

    def get_complexity(amount: float) -> str:
        if amount < 1000:
            return "simple"
        elif amount <= 5000:
            return "medium"
        else:
            return "complex"

    filtered = [
        s for s in scenarios
        if get_complexity(s.get("claim_amount", 0)) == level
    ]

    return {
        "scenarios": filtered,
        "count": len(filtered),
        "complexity": level,
    }


@router.get("/category/{category}")
async def get_scenarios_by_category(category: str):
    """
    Get scenarios filtered by claim category.

    Categories include: Emergency, Dental, Preventive, Illness,
    Orthopedic, Toxicity/Poisoning, etc.
    """
    scenarios = load_scenarios()

    # Case-insensitive partial match
    category_lower = category.lower()
    filtered = [
        s for s in scenarios
        if category_lower in s.get("claim_category", "").lower()
    ]

    return {
        "scenarios": filtered,
        "count": len(filtered),
        "category": category,
    }
