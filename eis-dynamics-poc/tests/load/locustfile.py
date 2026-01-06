"""
Load testing with Locust for EIS-Dynamics POC.

Run with:
    locust -f tests/load/locustfile.py --host=http://localhost:8000

For headless mode:
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \
        --headless -u 100 -r 10 -t 5m

Performance Targets:
    - API latency (p95): < 500ms
    - Quote calculation: < 2s
    - FNOL processing: < 3s (with AI)
    - Concurrent users: 100+
"""

from locust import HttpUser, task, between, events
from datetime import date, datetime
import json
import random
import string


def random_string(length: int = 8) -> str:
    """Generate random string for test data."""
    return "".join(random.choices(string.ascii_lowercase, k=length))


def random_phone() -> str:
    """Generate random phone number."""
    return f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"


def random_date_of_birth() -> str:
    """Generate random DOB for adult driver."""
    year = random.randint(1960, 2000)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year}-{month:02d}-{day:02d}"


def random_vehicle_year() -> int:
    """Generate random vehicle year."""
    return random.randint(2015, 2024)


class EISAPIUser(HttpUser):
    """
    Simulates an agent user interacting with the EIS-Dynamics APIs.
    """

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Initialize user session."""
        self.policy_ids = []
        self.claim_numbers = []
        self.customer_ids = []

    # =========================================================================
    # WS3: Integration Layer - Mock EIS APIs
    # =========================================================================

    @task(10)
    def get_policies(self):
        """Fetch list of policies."""
        with self.client.get(
            "/api/eis/policies",
            name="/api/eis/policies",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    self.policy_ids = [p["policy_id"] for p in data[:10]]
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(5)
    def get_policy_detail(self):
        """Fetch single policy details."""
        if not self.policy_ids:
            return

        policy_id = random.choice(self.policy_ids)
        with self.client.get(
            f"/api/eis/policies/{policy_id}",
            name="/api/eis/policies/[id]",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()  # Expected for some IDs
            else:
                response.failure(f"Status: {response.status_code}")

    @task(8)
    def get_customers(self):
        """Fetch list of customers."""
        with self.client.get(
            "/api/eis/customers",
            name="/api/eis/customers",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    self.customer_ids = [c["customer_id"] for c in data[:10]]
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(3)
    def get_customer_detail(self):
        """Fetch single customer details."""
        if not self.customer_ids:
            return

        customer_id = random.choice(self.customer_ids)
        with self.client.get(
            f"/api/eis/customers/{customer_id}",
            name="/api/eis/customers/[id]",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    # =========================================================================
    # WS2: AI Claims Service
    # =========================================================================

    @task(8)
    def get_claims(self):
        """Fetch list of claims."""
        with self.client.get(
            "/api/claims/",
            name="/api/claims/",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    self.claim_numbers = [c["claim_number"] for c in data[:10]]
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(4)
    def get_claim_detail(self):
        """Fetch single claim details."""
        if not self.claim_numbers:
            return

        claim_number = random.choice(self.claim_numbers)
        with self.client.get(
            f"/api/claims/{claim_number}",
            name="/api/claims/[id]",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(2)
    def submit_fnol(self):
        """Submit a new FNOL claim."""
        descriptions = [
            "I was rear-ended at a stoplight on Main Street. The other driver admitted fault.",
            "My car was hit while parked in a grocery store parking lot. No witnesses.",
            "Collision at intersection. Other driver ran red light. Police report filed.",
            "Single vehicle accident, hit a deer on highway. Minor front-end damage.",
            "Fender bender in drive-through lane. Very minor damage to bumper.",
        ]

        fnol_data = {
            "description": random.choice(descriptions),
            "date_of_loss": date.today().isoformat(),
            "policy_number": f"AUTO-{random.choice(['IL', 'CA', 'TX'])}-2024-{random.randint(10000, 99999)}",
            "contact_phone": random_phone(),
            "contact_email": f"{random_string()}@example.com",
        }

        with self.client.post(
            "/api/claims/fnol",
            json=fnol_data,
            name="/api/claims/fnol",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                data = response.json()
                if "claim_number" in data:
                    self.claim_numbers.append(data["claim_number"])
                response.success()
            elif response.status_code == 422:
                response.success()  # Validation error is expected sometimes
            else:
                response.failure(f"Status: {response.status_code}")

    # =========================================================================
    # WS5: Rating Engine
    # =========================================================================

    @task(6)
    def get_rating_factors(self):
        """Fetch current rating factors."""
        with self.client.get(
            "/api/rating/factors",
            name="/api/rating/factors",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(3)
    def calculate_quote(self):
        """Request a new insurance quote."""
        quote_data = {
            "state": random.choice(["IL", "CA", "TX", "NY", "FL", "OH", "PA"]),
            "zip_code": f"{random.randint(10000, 99999)}",
            "effective_date": date.today().isoformat(),
            "drivers": [
                {
                    "first_name": random_string(6).capitalize(),
                    "last_name": random_string(8).capitalize(),
                    "date_of_birth": random_date_of_birth(),
                    "gender": random.choice(["male", "female"]),
                    "marital_status": random.choice(["single", "married"]),
                    "license_date": f"{random.randint(1990, 2020)}-{random.randint(1, 12):02d}-01",
                    "violations": random.randint(0, 3),
                    "at_fault_accidents": random.randint(0, 2),
                    "is_primary": True,
                }
            ],
            "vehicles": [
                {
                    "year": random_vehicle_year(),
                    "make": random.choice(["Toyota", "Honda", "Ford", "Chevrolet", "BMW"]),
                    "model": random.choice(["Camry", "Accord", "F-150", "Malibu", "3 Series"]),
                    "body_type": random.choice(["sedan", "suv", "truck"]),
                    "use": random.choice(["commute", "pleasure", "business"]),
                    "annual_miles": random.randint(5000, 25000),
                    "anti_theft": random.choice([True, False]),
                    "safety_features": random.sample(
                        ["abs", "airbags", "backup_camera", "lane_assist"],
                        k=random.randint(1, 4)
                    ),
                }
            ],
            "coverages": [
                {"coverage_type": "bodily_injury", "limit": random.choice([50000, 100000, 250000]), "deductible": 0},
                {"coverage_type": "property_damage", "limit": random.choice([25000, 50000, 100000]), "deductible": 0},
                {"coverage_type": "collision", "limit": 0, "deductible": random.choice([250, 500, 1000])},
                {"coverage_type": "comprehensive", "limit": 0, "deductible": random.choice([100, 250, 500])},
            ],
            "prior_insurance": random.choice([True, False]),
            "homeowner": random.choice([True, False]),
            "multi_policy": random.choice([True, False]),
        }

        with self.client.post(
            "/api/rating/quote",
            json=quote_data,
            name="/api/rating/quote",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                data = response.json()
                if "total_premium" in data and data["total_premium"] > 0:
                    response.success()
                else:
                    response.failure("Invalid premium response")
            elif response.status_code == 422:
                response.success()  # Validation error
            else:
                response.failure(f"Status: {response.status_code}")

    # =========================================================================
    # Sync Operations
    # =========================================================================

    @task(1)
    def trigger_sync(self):
        """Trigger a sync operation."""
        sync_data = {
            "entity_type": random.choice(["policy", "claim", "customer"]),
            "direction": "eis_to_d365",
        }

        with self.client.post(
            "/api/sync/trigger",
            json=sync_data,
            name="/api/sync/trigger",
            catch_response=True
        ) as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


class HighVolumeQuoteUser(HttpUser):
    """
    Specialized user for high-volume quote testing.
    Simulates peak quote request periods.
    """

    wait_time = between(0.5, 1.5)
    weight = 3  # Higher weight for more quote traffic

    @task
    def rapid_quote_requests(self):
        """Submit quote requests rapidly."""
        quote_data = {
            "state": random.choice(["IL", "CA", "TX"]),
            "zip_code": "60601",
            "effective_date": date.today().isoformat(),
            "drivers": [{
                "first_name": "Test",
                "last_name": "Driver",
                "date_of_birth": "1985-01-15",
                "gender": "male",
                "marital_status": "married",
                "license_date": "2003-01-15",
                "violations": 0,
                "at_fault_accidents": 0,
                "is_primary": True,
            }],
            "vehicles": [{
                "year": 2022,
                "make": "Toyota",
                "model": "Camry",
                "body_type": "sedan",
                "use": "commute",
                "annual_miles": 12000,
                "anti_theft": True,
                "safety_features": ["abs", "airbags"],
            }],
            "coverages": [
                {"coverage_type": "bodily_injury", "limit": 100000, "deductible": 0},
                {"coverage_type": "property_damage", "limit": 50000, "deductible": 0},
            ],
            "prior_insurance": True,
            "homeowner": True,
            "multi_policy": False,
        }

        with self.client.post(
            "/api/rating/quote",
            json=quote_data,
            name="/api/rating/quote [high-volume]",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


# Custom event handlers for metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log slow requests for analysis."""
    if response_time > 500:  # Log requests slower than 500ms
        print(f"SLOW REQUEST: {name} took {response_time:.0f}ms")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print summary stats at end of test."""
    stats = environment.stats
    print("\n" + "=" * 60)
    print("LOAD TEST SUMMARY")
    print("=" * 60)

    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    avg_response = stats.total.avg_response_time
    p95_response = stats.total.get_response_time_percentile(0.95)

    print(f"Total Requests: {total_requests}")
    print(f"Failed Requests: {total_failures} ({total_failures/max(1,total_requests)*100:.1f}%)")
    print(f"Avg Response Time: {avg_response:.0f}ms")
    print(f"P95 Response Time: {p95_response:.0f}ms")

    # Check against SLAs
    print("\nSLA Compliance:")
    if p95_response <= 500:
        print("  [PASS] P95 latency <= 500ms")
    else:
        print(f"  [FAIL] P95 latency {p95_response:.0f}ms > 500ms")

    if total_failures / max(1, total_requests) <= 0.01:
        print("  [PASS] Error rate <= 1%")
    else:
        print(f"  [FAIL] Error rate {total_failures/max(1,total_requests)*100:.1f}% > 1%")

    print("=" * 60)
