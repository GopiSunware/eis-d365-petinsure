"""
PetInsure360 - Insights Service
Provides BI analytics data from the Gold layer.

Supports two modes:
1. Synapse Mode: Connects to Azure Synapse Serverless SQL for production
2. Local Mode: Uses local CSV/JSON files for development/demo

Configure via environment variables:
- USE_LOCAL_DATA=true/false (default: true)
- SYNAPSE_SERVER, SYNAPSE_DATABASE, SYNAPSE_USER, SYNAPSE_PASSWORD
"""

import os
import json
import math
import numpy as np
import pandas as pd
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def clean_for_json(data: Any) -> Any:
    """Clean data for JSON serialization by replacing NaN/Infinity values."""
    if data is None:
        return None
    if isinstance(data, dict):
        return {k: clean_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_for_json(item) for item in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    elif isinstance(data, (np.floating,)):
        if np.isnan(data) or np.isinf(data):
            return None
        return float(data)
    elif isinstance(data, (np.integer,)):
        return int(data)
    elif isinstance(data, np.bool_):
        return bool(data)
    elif isinstance(data, (pd.Timestamp, datetime)):
        return data.isoformat()
    elif isinstance(data, date):
        return data.isoformat()
    elif isinstance(data, pd.Categorical):
        return str(data) if pd.notna(data) else None
    elif pd.isna(data):
        return None
    return data


def safe_str(val: Any) -> str:
    """Safely convert value to string, handling NaN."""
    if pd.isna(val):
        return ""
    return str(val)


class InsightsService:
    """Service for querying Gold layer insights."""

    def __init__(self, data_path: str = None):
        """Initialize insights service with data path or Synapse connection."""
        # Check if we should use local data or Synapse
        self.use_local_data = os.getenv('USE_LOCAL_DATA', 'true').lower() == 'true'
        self.synapse_connection = None
        self.data_source = 'local'  # Track data source for pipeline UI

        if data_path is None:
            # Look for data in multiple locations
            possible_paths = [
                Path(__file__).parent.parent.parent.parent / "data" / "raw",
                Path("data/raw"),
                Path("../data/raw"),
            ]
            for p in possible_paths:
                if p.exists():
                    self.data_path = p
                    break
            else:
                self.data_path = Path("data/raw")
        else:
            self.data_path = Path(data_path)

        # Load and cache data
        self._customers = None
        self._pets = None
        self._policies = None
        self._claims = None
        self._providers = None

        # Pipeline metrics for visualization
        self._pipeline_metrics = {
            'bronze_count': 0,
            'silver_count': 0,
            'gold_count': 0,
            'last_refresh': None,
            'data_source': 'local'
        }

        self._load_data()

    def _get_synapse_connection(self):
        """Get Synapse SQL connection using pyodbc."""
        if self.synapse_connection is not None:
            return self.synapse_connection

        try:
            import pyodbc

            server = os.getenv('SYNAPSE_SERVER')
            database = os.getenv('SYNAPSE_DATABASE')
            username = os.getenv('SYNAPSE_USER')
            password = os.getenv('SYNAPSE_PASSWORD')

            if not all([server, database, username, password]):
                print("Synapse credentials not configured, using local data")
                return None

            connection_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
                f"Encrypt=yes;"
                f"TrustServerCertificate=no;"
                f"Connection Timeout=30;"
            )

            self.synapse_connection = pyodbc.connect(connection_string)
            print(f"Connected to Synapse: {server}/{database}")
            return self.synapse_connection

        except ImportError:
            print("pyodbc not installed, using local data")
            return None
        except Exception as e:
            print(f"Failed to connect to Synapse: {e}")
            return None

    def _load_from_synapse(self) -> bool:
        """Load data from Synapse Gold layer views."""
        conn = self._get_synapse_connection()
        if conn is None:
            return False

        try:
            # Load from Gold layer views
            print("Loading data from Synapse Gold layer...")

            self._customers = pd.read_sql("SELECT * FROM dbo.vw_customer_360", conn)
            print(f"Loaded {len(self._customers)} customers from Synapse")

            # For claims, use the claims_analytics view
            self._claims = pd.read_sql("SELECT * FROM dbo.vw_claims_analytics", conn)
            print(f"Loaded {len(self._claims)} claims from Synapse")

            # Load monthly KPIs directly from view
            self._monthly_kpis = pd.read_sql("SELECT * FROM dbo.vw_monthly_kpis", conn)
            print(f"Loaded {len(self._monthly_kpis)} monthly KPI records from Synapse")

            # Load pets and policies from Silver layer (if views exist)
            try:
                self._pets = pd.read_sql("SELECT * FROM petinsure_silver.dim_pets", conn)
                print(f"Loaded {len(self._pets)} pets from Synapse")
            except Exception:
                self._pets = pd.DataFrame()

            try:
                self._policies = pd.read_sql("SELECT * FROM petinsure_silver.dim_policies", conn)
                print(f"Loaded {len(self._policies)} policies from Synapse")
            except Exception:
                self._policies = pd.DataFrame()

            try:
                self._providers = pd.read_sql("SELECT * FROM petinsure_silver.dim_vet_providers", conn)
                print(f"Loaded {len(self._providers)} providers from Synapse")
            except Exception:
                self._providers = pd.DataFrame()

            self.data_source = 'synapse'
            self._pipeline_metrics['data_source'] = 'synapse'
            self._pipeline_metrics['last_refresh'] = datetime.now().isoformat()
            return True

        except Exception as e:
            print(f"Error loading from Synapse: {e}")
            return False

    def _load_data(self):
        """Load data from Synapse (production) or local files (development)."""
        # Try Synapse first if configured
        if not self.use_local_data:
            if self._load_from_synapse():
                print("Successfully loaded data from Synapse Gold layer")
                return

        # Fall back to local CSV/JSON files
        print("Loading data from local files...")
        self.data_source = 'local'
        self._pipeline_metrics['data_source'] = 'local'

        try:
            # Load customers
            customers_path = self.data_path / "customers.csv"
            if customers_path.exists():
                self._customers = pd.read_csv(customers_path)
                print(f"Loaded {len(self._customers)} customers from local files")

            # Load pets
            pets_path = self.data_path / "pets.csv"
            if pets_path.exists():
                self._pets = pd.read_csv(pets_path)
                print(f"Loaded {len(self._pets)} pets")

            # Load policies
            policies_path = self.data_path / "policies.csv"
            if policies_path.exists():
                self._policies = pd.read_csv(policies_path)
                print(f"Loaded {len(self._policies)} policies")

            # Load claims (JSON Lines)
            claims_path = self.data_path / "claims.jsonl"
            if claims_path.exists():
                claims_list = []
                with open(claims_path, 'r') as f:
                    for line in f:
                        claims_list.append(json.loads(line))
                self._claims = pd.DataFrame(claims_list)
                print(f"Loaded {len(self._claims)} claims")

            # Load providers
            providers_path = self.data_path / "vet_providers.csv"
            if providers_path.exists():
                self._providers = pd.read_csv(providers_path)
                print(f"Loaded {len(self._providers)} providers")

        except Exception as e:
            print(f"Error loading data: {e}")

    def _ensure_data(self):
        """Ensure data is loaded."""
        if self._customers is None:
            self._load_data()

    def _filter_by_customer(self, df: pd.DataFrame, customer_id: str) -> pd.DataFrame:
        """Safely filter DataFrame by customer_id."""
        if df is None or len(df) == 0:
            return pd.DataFrame()

        # Ensure customer_id column exists
        if 'customer_id' not in df.columns:
            return pd.DataFrame()

        # Convert to string for comparison
        df_copy = df.copy()
        df_copy['customer_id'] = df_copy['customer_id'].astype(str)

        result = df_copy[df_copy['customer_id'] == str(customer_id)]
        return result

    # Monthly KPIs
    def get_monthly_kpis(self, limit: int = 12) -> List[Dict[str, Any]]:
        """Get monthly KPI aggregations."""
        self._ensure_data()
        if self._claims is None or len(self._claims) == 0:
            return self._generate_sample_kpis(limit)

        df = self._claims.copy()
        df['service_date'] = pd.to_datetime(df['service_date'], errors='coerce')
        df = df.dropna(subset=['service_date'])
        df['year_month'] = df['service_date'].dt.to_period('M').astype(str)

        # Aggregate by month
        monthly = df.groupby('year_month').agg(
            total_claims=('claim_id', 'count'),
            unique_customers=('customer_id', 'nunique'),
            total_claim_amount=('claim_amount', 'sum'),
            total_paid_amount=('paid_amount', 'sum'),
            avg_processing_days=('processing_days', 'mean')
        ).reset_index()

        # Calculate rates
        status_counts = df.groupby(['year_month', 'status']).size().unstack(fill_value=0)
        if 'Approved' in status_counts.columns:
            monthly['approved_count'] = status_counts.get('Approved', 0).values
        else:
            monthly['approved_count'] = 0
        if 'Denied' in status_counts.columns:
            monthly['denied_count'] = status_counts.get('Denied', 0).values
        else:
            monthly['denied_count'] = 0

        monthly['approval_rate'] = (monthly['approved_count'] / monthly['total_claims'].replace(0, 1) * 100).round(2)
        monthly['denial_rate'] = (monthly['denied_count'] / monthly['total_claims'].replace(0, 1) * 100).round(2)
        monthly['loss_ratio'] = (monthly['total_paid_amount'] / monthly['total_claim_amount'].replace(0, 1) * 100).round(2)

        # Calculate growth
        monthly['prev_claims'] = monthly['total_claims'].shift(1)
        monthly['claims_growth_pct'] = (
            (monthly['total_claims'] - monthly['prev_claims']) / monthly['prev_claims'].replace(0, 1) * 100
        ).round(2)

        result = monthly.sort_values('year_month', ascending=False).head(limit)
        return clean_for_json(result.to_dict('records'))

    def _generate_sample_kpis(self, limit: int) -> List[Dict[str, Any]]:
        """Generate sample KPI data if no data is loaded."""
        import random
        kpis = []
        base_date = datetime.now()
        for i in range(limit):
            month = (base_date.month - i - 1) % 12 + 1
            year = base_date.year - ((base_date.month - i - 1) // 12)
            kpis.append({
                "year_month": f"{year}-{month:02d}",
                "total_claims": random.randint(1000, 1500),
                "unique_customers": random.randint(800, 1200),
                "total_claim_amount": round(random.uniform(300000, 500000), 2),
                "total_paid_amount": round(random.uniform(200000, 350000), 2),
                "approval_rate": round(random.uniform(70, 85), 2),
                "denial_rate": round(random.uniform(10, 20), 2),
                "avg_processing_days": round(random.uniform(3, 7), 1),
                "loss_ratio": round(random.uniform(60, 75), 2),
                "claims_growth_pct": round(random.uniform(-5, 10), 2)
            })
        return kpis

    # Customer 360
    def get_customer_360(self, customer_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get customer 360 view."""
        self._ensure_data()
        if self._customers is None or len(self._customers) == 0:
            return []

        # Merge customer data with aggregations
        customers = self._customers.copy()

        # Ensure customer_id is string type for consistent merging
        customers['customer_id'] = customers['customer_id'].astype(str)

        # Add pet counts
        if self._pets is not None and len(self._pets) > 0:
            pets_df = self._pets.copy()
            pets_df['customer_id'] = pets_df['customer_id'].astype(str)
            pet_counts = pets_df.groupby('customer_id').agg(
                total_pets=('pet_id', 'count')
            ).reset_index()
            customers = customers.merge(pet_counts, on='customer_id', how='left')
            customers['total_pets'] = customers['total_pets'].fillna(0).astype(int)
        else:
            customers['total_pets'] = 0

        # Add policy aggregations
        if self._policies is not None and len(self._policies) > 0:
            policies_df = self._policies.copy()
            policies_df['customer_id'] = policies_df['customer_id'].astype(str)
            policy_agg = policies_df.groupby('customer_id').agg(
                total_policies=('policy_id', 'count'),
                active_policies=('status', lambda x: (x == 'Active').sum()),
                total_annual_premium=('monthly_premium', lambda x: x.sum() * 12)
            ).reset_index()
            customers = customers.merge(policy_agg, on='customer_id', how='left')
            customers['total_policies'] = customers['total_policies'].fillna(0).astype(int)
            customers['active_policies'] = customers['active_policies'].fillna(0).astype(int)
            customers['total_annual_premium'] = customers['total_annual_premium'].fillna(0)
        else:
            customers['total_policies'] = 0
            customers['active_policies'] = 0
            customers['total_annual_premium'] = 0

        # Add claims aggregations
        if self._claims is not None and len(self._claims) > 0:
            claims_df = self._claims.copy()
            claims_df['customer_id'] = claims_df['customer_id'].astype(str)
            # Convert submission_date to datetime for max calculation (use service_date as fallback)
            date_col = 'submission_date' if 'submission_date' in claims_df.columns else 'service_date'
            claims_df['_claim_date'] = pd.to_datetime(claims_df[date_col], errors='coerce')
            claims_agg = claims_df.groupby('customer_id').agg(
                total_claims=('claim_id', 'count'),
                total_claim_amount=('claim_amount', 'sum'),
                total_paid_amount=('paid_amount', 'sum'),
                last_claim_date=('_claim_date', 'max')  # Track most recent claim
            ).reset_index()
            customers = customers.merge(claims_agg, on='customer_id', how='left')
            customers['total_claims'] = customers['total_claims'].fillna(0).astype(int)
            customers['total_claim_amount'] = customers['total_claim_amount'].fillna(0)
            customers['total_paid_amount'] = customers['total_paid_amount'].fillna(0)
        else:
            customers['total_claims'] = 0
            customers['total_claim_amount'] = 0
            customers['total_paid_amount'] = 0
            customers['last_claim_date'] = pd.NaT

        # Calculate derived metrics
        customers['loss_ratio'] = (
            customers['total_paid_amount'] / customers['total_annual_premium'].replace(0, 1) * 100
        ).round(2)

        # Customer value tier - handle NaN by replacing with default 'Bronze'
        customers['customer_value_tier'] = pd.cut(
            customers['total_annual_premium'].fillna(0),
            bins=[-1, 500, 1000, 2000, float('inf')],
            labels=['Bronze', 'Silver', 'Gold', 'Platinum']
        ).astype(str).replace('nan', 'Bronze')

        # Risk score - handle NaN by replacing with default 'Low'
        customers['customer_risk_score'] = pd.cut(
            customers['loss_ratio'].fillna(0),
            bins=[-1, 50, 75, 100, float('inf')],
            labels=['Low', 'Medium', 'High', 'Critical']
        ).astype(str).replace('nan', 'Low')

        # Churn risk
        customers['churn_risk'] = 'Low'  # Simplified

        # Add full name - handle NaN safely
        customers['full_name'] = customers['first_name'].fillna('') + ' ' + customers['last_name'].fillna('')
        customers['full_name'] = customers['full_name'].str.strip()

        # Filter by customer_id if provided
        if customer_id:
            customers = customers[customers['customer_id'].astype(str) == str(customer_id)]

        # Select columns
        columns = [
            'customer_id', 'full_name', 'first_name', 'last_name', 'email', 'phone', 'city', 'state',
            'customer_since', 'total_pets', 'total_policies', 'active_policies',
            'total_annual_premium', 'total_claims', 'total_claim_amount',
            'total_paid_amount', 'loss_ratio', 'customer_value_tier',
            'customer_risk_score', 'churn_risk'
        ]

        available_cols = [c for c in columns if c in customers.columns]

        # Sort by last_claim_date first (customers with recent claims at top),
        # then by customer_since (newest registrations next)
        # This ensures active customers appear first regardless of registration date
        if 'last_claim_date' in customers.columns:
            customers['_activity_date'] = customers['last_claim_date']
        else:
            customers['_activity_date'] = pd.NaT

        if 'customer_since' in customers.columns:
            customers['_reg_date'] = pd.to_datetime(customers['customer_since'], errors='coerce')
        else:
            customers['_reg_date'] = pd.NaT

        # Sort: customers with claims first (by last_claim_date desc), then by registration date
        customers = customers.sort_values(
            ['_activity_date', '_reg_date'],
            ascending=[False, False],
            na_position='last'
        )
        customers = customers.drop(columns=['_activity_date', '_reg_date', 'last_claim_date'], errors='ignore')

        result = customers[available_cols].head(limit)
        return clean_for_json(result.to_dict('records'))

    # Get pets for a customer
    def get_customer_pets(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all pets for a specific customer."""
        self._ensure_data()
        if self._pets is None:
            return []

        filtered = self._filter_by_customer(self._pets, customer_id)
        return clean_for_json(filtered.to_dict('records'))

    # Get policies for a customer
    def get_customer_policies(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all policies for a specific customer."""
        self._ensure_data()
        if self._policies is None:
            return []

        filtered = self._filter_by_customer(self._policies, customer_id)
        return clean_for_json(filtered.to_dict('records'))

    def get_all_policies(self) -> List[Dict[str, Any]]:
        """Get all policies in the system."""
        self._ensure_data()
        if self._policies is None:
            return []
        return clean_for_json(self._policies.to_dict('records'))

    # Get claims for a customer
    def get_customer_claims(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all claims for a specific customer."""
        self._ensure_data()
        if self._claims is None:
            return []

        filtered = self._filter_by_customer(self._claims, customer_id)
        return clean_for_json(filtered.to_dict('records'))

    # Claims Analytics
    def get_claims_analytics(
        self,
        status: str = None,
        category: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get claims analytics with filters."""
        self._ensure_data()
        if self._claims is None:
            return []

        df = self._claims.copy()

        # Join with customers for names
        if self._customers is not None:
            df = df.merge(
                self._customers[['customer_id', 'first_name', 'last_name']],
                on='customer_id',
                how='left'
            )
            df['customer_name'] = df['first_name'].fillna('') + ' ' + df['last_name'].fillna('')

        # Join with pets
        if self._pets is not None:
            df = df.merge(
                self._pets[['pet_id', 'pet_name', 'species']],
                on='pet_id',
                how='left'
            )

        # Join with providers
        if self._providers is not None:
            df = df.merge(
                self._providers[['provider_id', 'provider_name', 'is_in_network']],
                on='provider_id',
                how='left'
            )

        # Apply filters
        if status:
            df = df[df['status'] == status]
        if category:
            df = df[df['claim_category'] == category]

        # Select columns
        columns = [
            'claim_id', 'claim_number', 'customer_name', 'pet_name', 'species',
            'claim_type', 'claim_category', 'service_date', 'submission_date',
            'claim_amount', 'paid_amount', 'status', 'processing_days',
            'provider_name', 'is_in_network'
        ]
        available_cols = [c for c in columns if c in df.columns]

        # Sort by newest first - use submission_date if available, otherwise service_date
        # For new claims (added via portal), submission_date will be today
        # For static data, use service_date as fallback
        if 'submission_date' in df.columns and 'service_date' in df.columns:
            df['_sort_date'] = df['submission_date'].fillna(df['service_date'])
        elif 'submission_date' in df.columns:
            df['_sort_date'] = df['submission_date'].fillna('1900-01-01')
        elif 'service_date' in df.columns:
            df['_sort_date'] = df['service_date'].fillna('1900-01-01')
        else:
            df['_sort_date'] = '1900-01-01'

        df = df.sort_values('_sort_date', ascending=False, na_position='last')
        df = df.drop(columns=['_sort_date'], errors='ignore')

        result = df[available_cols].iloc[offset:offset + limit]
        return clean_for_json(result.to_dict('records'))

    # Provider Performance
    def get_provider_performance(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get provider performance analytics."""
        self._ensure_data()
        if self._providers is None:
            return []

        providers = self._providers.copy()

        # Add claims aggregations
        if self._claims is not None:
            claims_agg = self._claims.groupby('provider_id').agg(
                total_claims=('claim_id', 'count'),
                total_claim_amount=('claim_amount', 'sum'),
                avg_claim_amount=('claim_amount', 'mean'),
                avg_processing_days=('processing_days', 'mean')
            ).reset_index()
            providers = providers.merge(claims_agg, on='provider_id', how='left')
            providers['total_claims'] = providers['total_claims'].fillna(0).astype(int)
            providers['total_claim_amount'] = providers['total_claim_amount'].fillna(0)
            providers['avg_claim_amount'] = providers['avg_claim_amount'].fillna(0).round(2)
            providers['avg_processing_days'] = providers['avg_processing_days'].fillna(0).round(1)

        columns = [
            'provider_id', 'provider_name', 'provider_type', 'city', 'state',
            'is_in_network', 'average_rating', 'total_claims', 'total_claim_amount',
            'avg_claim_amount', 'avg_processing_days'
        ]
        available_cols = [c for c in columns if c in providers.columns]

        result = providers[available_cols].sort_values('total_claims', ascending=False).head(limit)
        return clean_for_json(result.to_dict('records'))

    # Risk Scoring
    def get_risk_scores(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get customer risk scores."""
        customers = self.get_customer_360(limit=limit)

        risk_scores = []
        for c in customers:
            loss_ratio = c.get('loss_ratio') or 0
            claims_count = c.get('total_claims') or 0

            # Calculate risk factors
            claims_risk = min(claims_count / 10, 1) * 25
            loss_risk = min(loss_ratio / 100, 1) * 35

            total_risk = claims_risk + loss_risk + 20  # Base risk

            risk_category = 'Low' if total_risk < 40 else 'Medium' if total_risk < 60 else 'High' if total_risk < 80 else 'Critical'

            risk_scores.append({
                'customer_id': c.get('customer_id'),
                'full_name': c.get('full_name'),
                'total_risk_score': round(total_risk, 1),
                'risk_category': risk_category,
                'claims_frequency_risk': round(claims_risk, 1),
                'loss_ratio_risk': round(loss_risk, 1),
                'pet_age_risk': 10.0,
                'breed_risk': 10.0,
                'recommendation': 'Monitor' if risk_category in ['Medium', 'High'] else 'Standard renewal'
            })

        return risk_scores

    # Cross-sell Recommendations
    def get_cross_sell(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get cross-sell recommendations."""
        customers = self.get_customer_360(limit=limit)

        cross_sell = []
        for c in customers:
            tier = c.get('customer_value_tier') or 'Bronze'
            active = c.get('active_policies') or 0

            # Determine recommendation
            if tier in ['Gold', 'Platinum'] and active < 2:
                recommendation = 'Multi-Pet Discount'
                reason = 'High-value customer with single policy'
                opportunity = 300.0
            elif tier == 'Silver':
                recommendation = 'Wellness Add-on'
                reason = 'Medium-value customer eligible for wellness'
                opportunity = 180.0
            else:
                recommendation = 'Plan Upgrade'
                reason = 'Standard upgrade path'
                opportunity = 120.0

            cross_sell.append({
                'customer_id': c.get('customer_id'),
                'full_name': c.get('full_name'),
                'email': c.get('email'),
                'customer_value_tier': tier,
                'current_plans': ['Premium'] if tier == 'Platinum' else ['Standard'],
                'recommendation': recommendation,
                'recommendation_reason': reason,
                'estimated_revenue_opportunity': opportunity,
                'priority_score': 100 if tier == 'Platinum' else 75 if tier == 'Gold' else 50
            })

        # Sort by priority
        cross_sell.sort(key=lambda x: x['priority_score'], reverse=True)
        return cross_sell[:limit]

    # Summary stats
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        self._ensure_data()

        return {
            'total_customers': len(self._customers) if self._customers is not None else 0,
            'total_pets': len(self._pets) if self._pets is not None else 0,
            'total_policies': len(self._policies) if self._policies is not None else 0,
            'total_claims': len(self._claims) if self._claims is not None else 0,
            'total_providers': len(self._providers) if self._providers is not None else 0,
            'data_path': str(self.data_path)
        }

    # Real-time registration methods (add to in-memory data for demo)
    def add_customer(self, customer_data: Dict[str, Any]) -> None:
        """Add a new customer to in-memory data for real-time display."""
        self._ensure_data()
        if self._customers is None:
            self._customers = pd.DataFrame()

        # Get customer_since from either field name
        customer_since = customer_data.get('customer_since') or customer_data.get('registration_date') or datetime.now().strftime('%Y-%m-%d')

        new_row = pd.DataFrame([{
            'customer_id': str(customer_data.get('customer_id', '')),
            'first_name': str(customer_data.get('first_name', '')),
            'last_name': str(customer_data.get('last_name', '')),
            'email': str(customer_data.get('email', '')),
            'phone': str(customer_data.get('phone', '')),
            'address_line1': str(customer_data.get('address_line1', '') or customer_data.get('address', '')),
            'city': str(customer_data.get('city', '')),
            'state': str(customer_data.get('state', '')),
            'zip_code': str(customer_data.get('zip_code', '')),
            'customer_since': str(customer_since),
            'preferred_contact': str(customer_data.get('preferred_contact', 'email')),
            'marketing_opt_in': bool(customer_data.get('marketing_opt_in', False))
        }])
        self._customers = pd.concat([self._customers, new_row], ignore_index=True)
        print(f"Added customer {customer_data.get('customer_id')} to in-memory data. Total: {len(self._customers)}")

    def add_pet(self, pet_data: Dict[str, Any]) -> None:
        """Add a new pet to in-memory data for real-time display."""
        self._ensure_data()
        if self._pets is None:
            self._pets = pd.DataFrame()

        # Helper to safely get string value (handles None and enums)
        def safe_str(val):
            if val is None:
                return None
            val_str = str(val)
            # Handle enum-like strings (e.g., "Species.DOG" -> "Dog")
            if '.' in val_str and val_str.split('.')[0] in ['Species', 'Gender']:
                return val_str.split('.')[1].title()
            return val_str

        new_row = pd.DataFrame([{
            'pet_id': safe_str(pet_data.get('pet_id')),
            'customer_id': safe_str(pet_data.get('customer_id')),
            'pet_name': safe_str(pet_data.get('pet_name')),
            'species': safe_str(pet_data.get('species')),
            'breed': safe_str(pet_data.get('breed')),
            'date_of_birth': safe_str(pet_data.get('date_of_birth')),
            'gender': safe_str(pet_data.get('gender')),
            'weight_lbs': float(pet_data.get('weight_lbs', 0) or 0),
            'color': safe_str(pet_data.get('color')),
            'microchip_id': safe_str(pet_data.get('microchip_id')) if pet_data.get('microchip_id') else None,
            'is_spayed_neutered': bool(pet_data.get('is_spayed_neutered', False) or pet_data.get('is_neutered', False)),
            'pre_existing_conditions': safe_str(pet_data.get('pre_existing_conditions')) if pet_data.get('pre_existing_conditions') else None
        }])
        self._pets = pd.concat([self._pets, new_row], ignore_index=True)
        print(f"Added pet {pet_data.get('pet_id')} for customer {pet_data.get('customer_id')} to in-memory data. Total pets: {len(self._pets)}")

    def add_policy(self, policy_data: Dict[str, Any]) -> None:
        """Add a new policy to in-memory data for real-time display."""
        self._ensure_data()
        if self._policies is None:
            self._policies = pd.DataFrame()

        new_row = pd.DataFrame([{
            'policy_id': str(policy_data.get('policy_id', '')),
            'policy_number': str(policy_data.get('policy_number', policy_data.get('policy_id', ''))),
            'customer_id': str(policy_data.get('customer_id', '')),
            'pet_id': str(policy_data.get('pet_id', '')),
            'plan_type': str(policy_data.get('plan_type', '') or policy_data.get('plan_name', 'Standard')),
            'coverage_type': str(policy_data.get('coverage_type', 'Accident & Illness')),
            'start_date': str(policy_data.get('effective_date', datetime.now().strftime('%Y-%m-%d'))),
            'end_date': str(policy_data.get('end_date', '')),
            'monthly_premium': float(policy_data.get('monthly_premium', 0) or 0),
            'annual_deductible': float(policy_data.get('annual_deductible', 500) or 500),
            'reimbursement_percentage': float(policy_data.get('reimbursement_percentage', 80) or 80),
            'annual_limit': float(policy_data.get('annual_limit', 10000) or policy_data.get('coverage_limit', 10000) or 10000),
            'status': 'Active',
            'waiting_period_days': int(policy_data.get('waiting_period_days', 14) or 14)
        }])
        self._policies = pd.concat([self._policies, new_row], ignore_index=True)
        print(f"Added policy {policy_data.get('policy_id')} for customer {policy_data.get('customer_id')} to in-memory data. Total policies: {len(self._policies)}")

    def add_claim(self, claim_data: Dict[str, Any]) -> None:
        """Add a new claim to in-memory data for real-time display."""
        self._ensure_data()
        if self._claims is None:
            self._claims = pd.DataFrame()

        customer_id = str(claim_data.get('customer_id', ''))
        pet_id = str(claim_data.get('pet_id', ''))

        # Ensure customer exists in our data (for proper joins in analytics)
        if customer_id and self._customers is not None:
            existing_customer = self._customers[self._customers['customer_id'].astype(str) == customer_id]
            if existing_customer.empty:
                # Add a placeholder customer record for this new customer
                self.add_customer({
                    'customer_id': customer_id,
                    'first_name': 'Customer',
                    'last_name': customer_id.replace('CUST-', '').replace('DEMO-', ''),
                    'email': f'{customer_id.lower()}@petinsure360.com',
                    'phone': '555-0000',
                    'city': 'New City',
                    'state': 'TX',
                    'customer_since': datetime.now().strftime('%Y-%m-%d')
                })
                print(f"Created placeholder customer: {customer_id}")

        # Ensure pet exists in our data
        if pet_id and self._pets is not None:
            existing_pet = self._pets[self._pets['pet_id'].astype(str) == pet_id]
            if existing_pet.empty:
                # Add a placeholder pet record
                self.add_pet({
                    'pet_id': pet_id,
                    'customer_id': customer_id,
                    'pet_name': claim_data.get('pet_name', 'Pet'),
                    'species': claim_data.get('species', 'Dog'),
                    'breed': claim_data.get('breed', 'Mixed'),
                    'date_of_birth': '2020-01-01',
                    'gender': 'Unknown',
                    'weight_lbs': 30
                })
                print(f"Created placeholder pet: {pet_id}")

        # Use current timestamp for submission to ensure proper sorting (newest first)
        submission_timestamp = datetime.now().isoformat()
        # Always use today's date for service_date on new submissions
        today_date = datetime.now().strftime('%Y-%m-%d')

        # Get customer_name and pet_name from claim_data if provided
        customer_name = claim_data.get('customer_name', '')
        pet_name_val = claim_data.get('pet_name', '')

        new_row = pd.DataFrame([{
            'claim_id': str(claim_data.get('claim_id', '')),
            'claim_number': str(claim_data.get('claim_number', claim_data.get('claim_id', ''))),
            'policy_id': str(claim_data.get('policy_id', '')),
            'customer_id': customer_id,
            'customer_name': str(customer_name) if customer_name else None,  # Store directly for analytics
            'pet_id': pet_id,
            'pet_name': str(pet_name_val) if pet_name_val else None,  # Store directly for analytics
            'provider_id': str(claim_data.get('provider_id', 'PROV-0001')),
            'provider_name': str(claim_data.get('provider_name', '')),
            'service_date': today_date,  # Always use today's date for new claims
            'submission_date': submission_timestamp,  # Full ISO timestamp for sorting
            'claim_type': str(claim_data.get('claim_type', 'Illness')),
            'claim_category': str(claim_data.get('claim_category', 'Veterinary')),
            'diagnosis': str(claim_data.get('diagnosis', '') or claim_data.get('diagnosis_code', '')),
            'treatment_description': str(claim_data.get('treatment', '') or claim_data.get('treatment_notes', '')),
            'claim_amount': float(claim_data.get('claim_amount', 0) or 0),
            'paid_amount': float(claim_data.get('paid_amount', 0) or 0),
            'status': str(claim_data.get('status', 'Submitted')),
            'processing_days': int(claim_data.get('processing_days', 0) or 0),
            'is_in_network': bool(claim_data.get('is_in_network', True)),
            'is_emergency': bool(claim_data.get('is_emergency', False))
        }])
        self._claims = pd.concat([self._claims, new_row], ignore_index=True)
        print(f"Added claim {claim_data.get('claim_id')} for customer {customer_id} to in-memory data. Total claims: {len(self._claims)}")

    # Pipeline Status Methods (for Pipeline Visualization UI)
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current data pipeline status for visualization."""
        self._ensure_data()

        return {
            'data_source': self.data_source,
            'layers': {
                'bronze': {
                    'status': 'active',
                    'record_count': len(self._claims) if self._claims is not None else 0,
                    'description': 'Raw data ingestion from API',
                    'last_update': self._pipeline_metrics.get('last_refresh') or datetime.now().isoformat()
                },
                'silver': {
                    'status': 'active',
                    'record_count': len(self._customers) if self._customers is not None else 0,
                    'description': 'Cleaned and validated data',
                    'last_update': self._pipeline_metrics.get('last_refresh') or datetime.now().isoformat()
                },
                'gold': {
                    'status': 'active',
                    'record_count': len(self._customers) if self._customers is not None else 0,
                    'description': 'Business aggregations and analytics',
                    'last_update': self._pipeline_metrics.get('last_refresh') or datetime.now().isoformat()
                }
            },
            'metrics': {
                'total_customers': len(self._customers) if self._customers is not None else 0,
                'total_pets': len(self._pets) if self._pets is not None else 0,
                'total_policies': len(self._policies) if self._policies is not None else 0,
                'total_claims': len(self._claims) if self._claims is not None else 0,
                'total_providers': len(self._providers) if self._providers is not None else 0
            },
            'data_quality': {
                'completeness': 95.5,  # Would calculate from actual null counts
                'accuracy': 98.2,
                'freshness': 'Real-time' if self.data_source == 'synapse' else 'Cached'
            }
        }

    def get_pipeline_flow(self) -> Dict[str, Any]:
        """Get pipeline flow data for animated visualization."""
        return {
            'nodes': [
                {'id': 'api', 'label': 'API Ingestion', 'type': 'source', 'x': 0, 'y': 50},
                {'id': 'bronze', 'label': 'Bronze Layer', 'type': 'storage', 'x': 150, 'y': 50},
                {'id': 'databricks', 'label': 'Databricks', 'type': 'processing', 'x': 300, 'y': 50},
                {'id': 'silver', 'label': 'Silver Layer', 'type': 'storage', 'x': 450, 'y': 50},
                {'id': 'gold', 'label': 'Gold Layer', 'type': 'storage', 'x': 600, 'y': 50},
                {'id': 'synapse', 'label': 'Synapse SQL', 'type': 'query', 'x': 750, 'y': 50},
                {'id': 'dashboard', 'label': 'BI Dashboard', 'type': 'destination', 'x': 900, 'y': 50}
            ],
            'edges': [
                {'from': 'api', 'to': 'bronze', 'label': 'JSON/CSV'},
                {'from': 'bronze', 'to': 'databricks', 'label': 'Delta Lake'},
                {'from': 'databricks', 'to': 'silver', 'label': 'Transform'},
                {'from': 'silver', 'to': 'gold', 'label': 'Aggregate'},
                {'from': 'gold', 'to': 'synapse', 'label': 'External Tables'},
                {'from': 'synapse', 'to': 'dashboard', 'label': 'SQL Queries'}
            ],
            'active_flow': self.data_source == 'synapse'
        }

    def refresh_data(self) -> bool:
        """Force refresh of data from source."""
        self._customers = None
        self._pets = None
        self._policies = None
        self._claims = None
        self._providers = None
        self._load_data()
        self._pipeline_metrics['last_refresh'] = datetime.now().isoformat()
        return True

    async def load_persisted_demo_data(self, storage) -> dict:
        """
        Load persisted demo data from Azure Storage on startup.
        Returns count of loaded records per entity type.
        Prevents duplicates by checking existing IDs.
        """
        loaded_counts = {'customers': 0, 'pets': 0, 'claims': 0}

        try:
            self._ensure_data()

            # Get existing IDs to prevent duplicates
            existing_customer_ids = set()
            existing_pet_ids = set()
            existing_claim_ids = set()

            if self._customers is not None and len(self._customers) > 0:
                existing_customer_ids = set(self._customers['customer_id'].astype(str).tolist())
            if self._pets is not None and len(self._pets) > 0:
                existing_pet_ids = set(self._pets['pet_id'].astype(str).tolist())
            if self._claims is not None and len(self._claims) > 0:
                existing_claim_ids = set(self._claims['claim_id'].astype(str).tolist())

            # Load demo customers (skip duplicates)
            demo_customers = await storage.load_demo_data('customers')
            for customer in demo_customers:
                customer_id = str(customer.get('customer_id', ''))
                if customer_id and customer_id not in existing_customer_ids:
                    self.add_customer(customer)
                    existing_customer_ids.add(customer_id)
                    loaded_counts['customers'] += 1

            # Load demo pets (skip duplicates)
            demo_pets = await storage.load_demo_data('pets')
            for pet in demo_pets:
                pet_id = str(pet.get('pet_id', ''))
                if pet_id and pet_id not in existing_pet_ids:
                    self.add_pet(pet)
                    existing_pet_ids.add(pet_id)
                    loaded_counts['pets'] += 1

            # Load demo claims (skip duplicates)
            demo_claims = await storage.load_demo_data('claims')
            for claim in demo_claims:
                claim_id = str(claim.get('claim_id', ''))
                if claim_id and claim_id not in existing_claim_ids:
                    self.add_claim(claim)
                    existing_claim_ids.add(claim_id)
                    loaded_counts['claims'] += 1

            if any(loaded_counts.values()):
                print(f"Loaded persisted demo data: {loaded_counts}")

        except Exception as e:
            print(f"Error loading persisted demo data: {e}")
            import traceback
            traceback.print_exc()

        return loaded_counts
