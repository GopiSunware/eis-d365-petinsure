"""
Tools for the Agent Pipeline.

Provides tools for validation, enrichment, analytics, and storage operations.
Also includes 46 tools that call the Unified Claims Data API (port 8000).
"""

from .unified_api_tools import (
    # Tool collections for agents
    ALL_TOOLS as UNIFIED_API_ALL_TOOLS,
    BRONZE_TOOLS as UNIFIED_API_BRONZE_TOOLS,
    SILVER_TOOLS as UNIFIED_API_SILVER_TOOLS,
    GOLD_TOOLS as UNIFIED_API_GOLD_TOOLS,
    get_tools_for_agent,
    # Individual tools
    get_policy,
    check_coverage,
    get_policy_exclusions,
    check_policy_limits,
    get_waiting_periods,
    get_policy_history,
    get_customer,
    get_claim_history,
    get_customer_ltv,
    get_customer_risk_tier,
    get_communication_history,
    get_customer_household,
    get_pet_profile,
    get_pet_medical_history,
    get_pet_pre_existing_conditions,
    get_breed_risks,
    check_vaccination_status,
    verify_provider,
    get_provider_network_status,
    get_provider_stats,
    get_provider_fraud_rate,
    get_provider_peer_comparison,
    check_fraud_indicators,
    velocity_check,
    duplicate_check,
    fraud_pattern_match,
    provider_customer_analysis,
    calculate_fraud_score,
    validate_diagnosis_code,
    get_treatment_benchmarks,
    get_typical_treatment,
    check_related_conditions,
    get_breed_condition_risk,
    calculate_reimbursement,
    check_deductible_status,
    get_payment_history,
    check_payment_status,
    get_annual_summary,
)
from .analytics_tools import (
    GOLD_ANALYTICS_TOOLS,
    assess_risk,
    calculate_kpi_metrics,
    create_alerts,
    generate_insights,
    update_customer_360,
)
from .enrichment_tools import (
    SILVER_ENRICHMENT_TOOLS,
    apply_business_rules,
    calculate_quality_scores,
    enrich_claim,
    get_customer_claim_history,
    normalize_values,
)
from .storage_tools import (
    STORAGE_TOOLS,
    get_historical_claims,
    read_layer_data,
    update_kpi_aggregates,
    write_bronze,
    write_gold,
    write_silver,
)
from .validation_tools import (
    BRONZE_VALIDATION_TOOLS,
    assess_quality,
    clean_data,
    detect_anomalies,
    validate_schema,
)

__all__ = [
    # Unified API tools (46 tools calling port 8000)
    "UNIFIED_API_ALL_TOOLS",
    "UNIFIED_API_BRONZE_TOOLS",
    "UNIFIED_API_SILVER_TOOLS",
    "UNIFIED_API_GOLD_TOOLS",
    "get_tools_for_agent",
    # Policy tools
    "get_policy",
    "check_coverage",
    "get_policy_exclusions",
    "check_policy_limits",
    "get_waiting_periods",
    "get_policy_history",
    # Customer tools
    "get_customer",
    "get_claim_history",
    "get_customer_ltv",
    "get_customer_risk_tier",
    "get_communication_history",
    "get_customer_household",
    # Pet tools
    "get_pet_profile",
    "get_pet_medical_history",
    "get_pet_pre_existing_conditions",
    "get_breed_risks",
    "check_vaccination_status",
    # Provider tools
    "verify_provider",
    "get_provider_network_status",
    "get_provider_stats",
    "get_provider_fraud_rate",
    "get_provider_peer_comparison",
    # Fraud tools
    "check_fraud_indicators",
    "velocity_check",
    "duplicate_check",
    "fraud_pattern_match",
    "provider_customer_analysis",
    "calculate_fraud_score",
    # Medical tools
    "validate_diagnosis_code",
    "get_treatment_benchmarks",
    "get_typical_treatment",
    "check_related_conditions",
    "get_breed_condition_risk",
    # Billing tools
    "calculate_reimbursement",
    "check_deductible_status",
    "get_payment_history",
    "check_payment_status",
    "get_annual_summary",
    # Validation tools (Bronze) - Legacy
    "BRONZE_VALIDATION_TOOLS",
    "validate_schema",
    "detect_anomalies",
    "clean_data",
    "assess_quality",
    # Enrichment tools (Silver) - Legacy
    "SILVER_ENRICHMENT_TOOLS",
    "enrich_claim",
    "normalize_values",
    "apply_business_rules",
    "calculate_quality_scores",
    "get_customer_claim_history",
    # Analytics tools (Gold) - Legacy
    "GOLD_ANALYTICS_TOOLS",
    "assess_risk",
    "generate_insights",
    "calculate_kpi_metrics",
    "create_alerts",
    "update_customer_360",
    # Storage tools
    "STORAGE_TOOLS",
    "write_bronze",
    "write_silver",
    "write_gold",
    "read_layer_data",
    "get_historical_claims",
    "update_kpi_aggregates",
]
