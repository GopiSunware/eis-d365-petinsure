"""
PetInsure360 - Claim Scenarios API
Pre-defined claim scenarios for demo purposes
"""

import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter()

# Load scenarios from JSON file
SCENARIOS_FILE = Path(__file__).parent.parent.parent / "data" / "claim_scenarios.json"

def load_scenarios():
    """Load claim scenarios from JSON file with dynamic dates."""
    try:
        if SCENARIOS_FILE.exists():
            with open(SCENARIOS_FILE, 'r') as f:
                data = json.load(f)
                scenarios = data.get('scenarios', [])

                # Replace hardcoded dates with today's date for all scenarios
                today = datetime.now().strftime('%Y-%m-%d')
                for scenario in scenarios:
                    scenario['service_date'] = today

                return scenarios
        return []
    except Exception as e:
        print(f"Error loading scenarios: {e}")
        return []

@router.get("/")
async def get_all_scenarios():
    """Get all pre-defined claim scenarios."""
    scenarios = load_scenarios()
    return {
        "scenarios": scenarios,
        "count": len(scenarios)
    }

@router.get("/by-user/{email}")
async def get_scenarios_by_user(email: str):
    """Get scenarios filtered by demo user email."""
    scenarios = load_scenarios()
    filtered = [s for s in scenarios if s.get('demo_user') == email]
    return {
        "scenarios": filtered,
        "count": len(filtered),
        "user": email
    }

@router.get("/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get a specific scenario by ID."""
    scenarios = load_scenarios()
    for scenario in scenarios:
        if scenario.get('id') == scenario_id:
            return {"scenario": scenario}
    raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
