"""
ValidationService - AI-powered data quality and compliance validation.
5 validation categories that rules cannot catch.

Categories:
1. Diagnosis-Treatment Mismatch
2. Cross-Document Inconsistency
3. Claim Completeness & Sequence
4. License Verification (Regulatory)
5. Controlled Substance Compliance (Regulatory)
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.data_loader import get_data_store

router = APIRouter()


# =============================================================================
# REFERENCE DATA: Diagnosis-Treatment Mappings
# =============================================================================

DIAGNOSIS_TREATMENT_MAP = {
    # Diagnosis Code -> Expected treatments, contraindicated treatments, required prerequisites
    "S83.5": {  # CCL/ACL tear
        "description": "Cruciate Ligament Rupture",
        "expected_treatments": ["TPLO surgery", "TTA surgery", "Lateral suture", "Conservative management", "Physical therapy"],
        "expected_procedure_codes": ["SURG-TPLO", "SURG-TTA", "SURG-LS", "CONS-MGT", "PT-REHAB"],
        "required_diagnostics": ["X-ray", "Physical examination", "Sedation for exam"],
        "contraindicated": ["Dental cleaning", "Spay/Neuter", "Vaccination"],
        "typical_cost_range": [3000, 6500],
        "typical_duration_days": [1, 90],
        "severity": "surgical"
    },
    "K08.3": {  # Dental disease
        "description": "Dental/Periodontal Disease",
        "expected_treatments": ["Dental cleaning", "Tooth extraction", "Dental X-rays", "Antibiotics"],
        "expected_procedure_codes": ["DENT-CLN", "DENT-EXT", "DENT-XRAY", "MED-ANTI"],
        "required_diagnostics": ["Pre-anesthetic bloodwork", "Physical examination"],
        "contraindicated": ["Orthopedic surgery", "Chemotherapy"],
        "typical_cost_range": [300, 1500],
        "typical_duration_days": [1, 14],
        "severity": "moderate"
    },
    "N39.0": {  # UTI
        "description": "Urinary Tract Infection",
        "expected_treatments": ["Antibiotics", "Urinalysis", "Urine culture"],
        "expected_procedure_codes": ["MED-ANTI", "LAB-UA", "LAB-UCULT"],
        "required_diagnostics": ["Urinalysis", "Physical examination"],
        "contraindicated": ["Surgery", "Anesthesia", "Dental procedures"],
        "typical_cost_range": [150, 500],
        "typical_duration_days": [7, 21],
        "severity": "mild"
    },
    "E11.9": {  # Diabetes
        "description": "Diabetes Mellitus",
        "expected_treatments": ["Insulin therapy", "Glucose monitoring", "Dietary management", "Blood glucose curve"],
        "expected_procedure_codes": ["MED-INS", "LAB-GLUC", "CONS-DIET", "LAB-BGC"],
        "required_diagnostics": ["Blood glucose test", "Fructosamine test", "Urinalysis"],
        "contraindicated": ["Steroids", "High-carb diet recommendation"],
        "typical_cost_range": [500, 2000],
        "typical_duration_days": [1, 365],
        "severity": "chronic"
    },
    "G95.89": {  # IVDD
        "description": "Intervertebral Disc Disease",
        "expected_treatments": ["Spinal surgery", "MRI", "CT scan", "Cage rest", "Pain management", "Physical therapy"],
        "expected_procedure_codes": ["SURG-SPINE", "IMG-MRI", "IMG-CT", "CONS-REST", "MED-PAIN", "PT-REHAB"],
        "required_diagnostics": ["Neurological examination", "MRI or CT", "X-rays"],
        "contraindicated": ["Jumping exercises", "Chiropractic manipulation"],
        "typical_cost_range": [4000, 12000],
        "typical_duration_days": [1, 180],
        "severity": "emergency"
    },
    "T65.8": {  # Toxin ingestion
        "description": "Toxic Substance Ingestion",
        "expected_treatments": ["Decontamination", "IV fluids", "Activated charcoal", "Monitoring", "Antidote if available"],
        "expected_procedure_codes": ["ER-DECON", "FLUID-IV", "MED-CHAR", "HOSP-MON", "MED-ANTID"],
        "required_diagnostics": ["Bloodwork", "Toxin identification", "Physical examination"],
        "contraindicated": ["Induced vomiting after corrosives", "Delayed treatment"],
        "typical_cost_range": [500, 5000],
        "typical_duration_days": [1, 7],
        "severity": "emergency"
    },
    "Z00.0": {  # Wellness exam
        "description": "Routine Wellness Examination",
        "expected_treatments": ["Physical examination", "Vaccinations", "Preventive medications"],
        "expected_procedure_codes": ["EXAM-WELL", "VAC-CORE", "VAC-NON", "MED-PREV"],
        "required_diagnostics": [],
        "contraindicated": ["Surgery", "Emergency procedures", "Chemotherapy"],
        "typical_cost_range": [50, 250],
        "typical_duration_days": [1, 1],
        "severity": "preventive"
    },
    "L50.0": {  # Allergic reaction
        "description": "Allergic Reaction/Urticaria",
        "expected_treatments": ["Antihistamines", "Steroids", "Epinephrine if severe", "Monitoring"],
        "expected_procedure_codes": ["MED-ANTIH", "MED-STER", "MED-EPI", "HOSP-MON"],
        "required_diagnostics": ["Physical examination", "Allergy testing if recurrent"],
        "contraindicated": ["Vaccination same day", "Non-essential procedures"],
        "typical_cost_range": [100, 800],
        "typical_duration_days": [1, 7],
        "severity": "moderate"
    }
}

# =============================================================================
# REFERENCE DATA: Procedure Sequences
# =============================================================================

PROCEDURE_SEQUENCES = {
    # Procedure -> Required predecessors
    "SURG-TPLO": {
        "name": "TPLO Surgery",
        "required_before": ["EXAM-ORTHO", "IMG-XRAY", "LAB-PREANEST"],
        "required_before_names": ["Orthopedic examination", "X-rays", "Pre-anesthetic bloodwork"],
        "typical_gap_days": [0, 14],  # Must happen within 14 days of diagnostics
        "required_after": ["MED-PAIN", "PT-REHAB"],
        "required_after_names": ["Pain medication", "Physical therapy/rehab"]
    },
    "SURG-SPINE": {
        "name": "Spinal Surgery",
        "required_before": ["EXAM-NEURO", "IMG-MRI", "LAB-PREANEST"],
        "required_before_names": ["Neurological examination", "MRI imaging", "Pre-anesthetic bloodwork"],
        "typical_gap_days": [0, 7],
        "required_after": ["MED-PAIN", "HOSP-MON", "PT-REHAB"],
        "required_after_names": ["Pain medication", "Hospitalization monitoring", "Physical therapy"]
    },
    "DENT-CLN": {
        "name": "Dental Cleaning",
        "required_before": ["LAB-PREANEST", "EXAM-ORAL"],
        "required_before_names": ["Pre-anesthetic bloodwork", "Oral examination"],
        "typical_gap_days": [0, 30],
        "required_after": ["MED-ANTI"],
        "required_after_names": ["Antibiotics if extractions performed"]
    },
    "IMG-MRI": {
        "name": "MRI Imaging",
        "required_before": ["EXAM-NEURO"],
        "required_before_names": ["Neurological examination"],
        "typical_gap_days": [0, 7],
        "required_after": [],
        "required_after_names": []
    },
    "MED-CHEMO": {
        "name": "Chemotherapy",
        "required_before": ["LAB-CBC", "DIAG-BIOPSY", "IMG-STAGE"],
        "required_before_names": ["Complete blood count", "Biopsy/pathology", "Staging imaging"],
        "typical_gap_days": [0, 30],
        "required_after": ["LAB-CBC", "HOSP-MON"],
        "required_after_names": ["Follow-up blood count", "Monitoring for side effects"]
    }
}

# =============================================================================
# REFERENCE DATA: Controlled Substances
# =============================================================================

CONTROLLED_SUBSTANCES = {
    "Tramadol": {
        "schedule": "IV",
        "requires_dea": True,
        "max_days_supply": 30,
        "requires_diagnosis": True,
        "common_diagnoses": ["S83.5", "G95.89", "post-surgical"],
        "documentation_required": ["Pain assessment", "Weight-based dosing"]
    },
    "Gabapentin": {
        "schedule": "V",
        "requires_dea": True,
        "max_days_supply": 90,
        "requires_diagnosis": True,
        "common_diagnoses": ["G95.89", "neuropathic pain", "seizures"],
        "documentation_required": ["Neurological assessment"]
    },
    "Phenobarbital": {
        "schedule": "IV",
        "requires_dea": True,
        "max_days_supply": 90,
        "requires_diagnosis": True,
        "common_diagnoses": ["G40", "seizure disorder"],
        "documentation_required": ["Seizure history", "Blood level monitoring"]
    },
    "Ketamine": {
        "schedule": "III",
        "requires_dea": True,
        "max_days_supply": 1,
        "requires_diagnosis": True,
        "common_diagnoses": ["anesthesia", "sedation"],
        "documentation_required": ["Anesthesia record", "Monitoring logs"]
    },
    "Butorphanol": {
        "schedule": "IV",
        "requires_dea": True,
        "max_days_supply": 7,
        "requires_diagnosis": True,
        "common_diagnoses": ["pain management", "sedation", "cough"],
        "documentation_required": ["Pain assessment"]
    },
    "Hydrocodone": {
        "schedule": "II",
        "requires_dea": True,
        "max_days_supply": 14,
        "requires_diagnosis": True,
        "common_diagnoses": ["severe pain", "post-surgical"],
        "documentation_required": ["Pain assessment", "Treatment plan", "Client education"]
    }
}

# =============================================================================
# REFERENCE DATA: State Licensing Requirements
# =============================================================================

STATE_REQUIREMENTS = {
    "CA": {
        "license_prefix": "VET",
        "requires_facility_license": True,
        "controlled_substance_state_license": True,
        "telemedicine_restrictions": "Initial exam required in-person",
        "ce_hours_required": 36
    },
    "NY": {
        "license_prefix": "VET",
        "requires_facility_license": True,
        "controlled_substance_state_license": True,
        "telemedicine_restrictions": "VCPR must be established",
        "ce_hours_required": 45
    },
    "TX": {
        "license_prefix": "TX",
        "requires_facility_license": False,
        "controlled_substance_state_license": True,
        "telemedicine_restrictions": "Limited without VCPR",
        "ce_hours_required": 18
    },
    "FL": {
        "license_prefix": "VET",
        "requires_facility_license": True,
        "controlled_substance_state_license": True,
        "telemedicine_restrictions": "VCPR required",
        "ce_hours_required": 30
    }
}


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class ClaimValidationRequest(BaseModel):
    claim_id: str
    policy_id: str
    pet_id: str
    provider_id: str
    diagnosis_code: str
    diagnosis_description: Optional[str] = None
    procedure_codes: List[str] = []
    procedure_descriptions: List[str] = []
    medications: List[str] = []
    claim_amount: float
    service_date: str
    invoice_data: Optional[Dict[str, Any]] = None
    medical_record_data: Optional[Dict[str, Any]] = None


class ValidationResult(BaseModel):
    validation_type: str
    passed: bool
    severity: str  # info, warning, error, critical
    message: str
    details: Dict[str, Any] = {}
    recommendation: str = ""


# =============================================================================
# ENDPOINT 1: Diagnosis-Treatment Mismatch
# =============================================================================

@router.post("/diagnosis-treatment")
async def validate_diagnosis_treatment(request: ClaimValidationRequest) -> Dict[str, Any]:
    """
    Validate that treatments match the diagnosis.
    AI catches mismatches that rules cannot.

    LLM Tool: validate_diagnosis_treatment(claim_data)
    """
    issues = []
    warnings = []

    diagnosis_code = request.diagnosis_code
    procedures = request.procedure_descriptions or request.procedure_codes

    # Get diagnosis mapping
    diagnosis_info = DIAGNOSIS_TREATMENT_MAP.get(diagnosis_code)

    if not diagnosis_info:
        # Try partial match
        for code, info in DIAGNOSIS_TREATMENT_MAP.items():
            if diagnosis_code.startswith(code.split(".")[0]):
                diagnosis_info = info
                break

    if not diagnosis_info:
        return {
            "validation_type": "diagnosis_treatment_mismatch",
            "passed": True,
            "score": 100,
            "message": "Diagnosis code not in validation database - manual review recommended",
            "issues": [],
            "warnings": [{"type": "unknown_diagnosis", "message": f"Diagnosis {diagnosis_code} not in reference database"}]
        }

    # Check for expected treatments AND unexpected treatments
    expected = diagnosis_info["expected_treatments"]
    found_expected = []
    unexpected_procedures = []

    for proc in procedures:
        proc_lower = proc.lower()
        matched = False
        for exp in expected:
            if exp.lower() in proc_lower or proc_lower in exp.lower():
                found_expected.append(exp)
                matched = True
                break
        if not matched:
            unexpected_procedures.append(proc)

    if not found_expected and procedures:
        issues.append({
            "type": "no_expected_treatment",
            "severity": "warning",
            "message": f"None of the treatments {procedures} are typical for {diagnosis_info['description']}",
            "expected": expected,
            "found": procedures
        })

    # Flag unexpected/excessive procedures (like MRI for allergic reaction)
    if unexpected_procedures:
        issues.append({
            "type": "unexpected_procedure",
            "severity": "warning",
            "message": f"Procedure(s) not typical for {diagnosis_info['description']}: {unexpected_procedures}",
            "expected": expected,
            "unexpected": unexpected_procedures
        })

    # Check for contraindicated treatments
    contraindicated = diagnosis_info.get("contraindicated", [])
    found_contraindicated = []

    for proc in procedures:
        proc_lower = proc.lower()
        for contra in contraindicated:
            if contra.lower() in proc_lower:
                found_contraindicated.append(contra)

    if found_contraindicated:
        issues.append({
            "type": "contraindicated_treatment",
            "severity": "error",
            "message": f"Treatment(s) {found_contraindicated} contraindicated for {diagnosis_info['description']}",
            "contraindicated": contraindicated,
            "found": found_contraindicated
        })

    # Check cost range
    min_cost, max_cost = diagnosis_info["typical_cost_range"]
    if request.claim_amount < min_cost * 0.5:
        warnings.append({
            "type": "unusually_low_cost",
            "severity": "info",
            "message": f"Claim amount ${request.claim_amount} is below typical range ${min_cost}-${max_cost}",
            "typical_range": [min_cost, max_cost]
        })
    elif request.claim_amount > max_cost * 1.5:
        issues.append({
            "type": "unusually_high_cost",
            "severity": "warning",
            "message": f"Claim amount ${request.claim_amount} significantly exceeds typical range ${min_cost}-${max_cost}",
            "typical_range": [min_cost, max_cost]
        })

    # Calculate score
    score = 100
    for issue in issues:
        if issue["severity"] == "error":
            score -= 30
        elif issue["severity"] == "warning":
            score -= 15
    for warning in warnings:
        score -= 5

    score = max(0, score)

    return {
        "validation_type": "diagnosis_treatment_mismatch",
        "passed": len([i for i in issues if i["severity"] == "error"]) == 0,
        "score": score,
        "diagnosis": diagnosis_info["description"],
        "diagnosis_code": diagnosis_code,
        "severity_category": diagnosis_info["severity"],
        "issues": issues,
        "warnings": warnings,
        "expected_treatments": expected,
        "recommendation": "Manual review required" if score < 70 else "Proceed with processing"
    }


# =============================================================================
# ENDPOINT 2: Cross-Document Inconsistency
# =============================================================================

@router.post("/document-consistency")
async def validate_document_consistency(request: ClaimValidationRequest) -> Dict[str, Any]:
    """
    Compare invoice data vs medical records for inconsistencies.
    AI catches semantic mismatches that rules cannot.

    LLM Tool: validate_document_consistency(claim_data)
    """
    issues = []
    warnings = []

    invoice = request.invoice_data or {}
    medical_records = request.medical_record_data or {}

    # If no documents provided, use claim data as invoice proxy
    if not invoice:
        invoice = {
            "pet_name": None,
            "procedures": request.procedure_descriptions,
            "amount": request.claim_amount,
            "date": request.service_date,
            "diagnosis": request.diagnosis_description
        }

    # Get pet info for comparison
    store = get_data_store()
    pet = store.get_pet(request.pet_id)

    # Check 1: Pet name consistency
    invoice_pet_name = (invoice.get("pet_name") or "").lower().strip()
    record_pet_name = (medical_records.get("patient_name") or "").lower().strip()
    policy_pet_name = (pet.get("name") or "").lower().strip() if pet else ""

    if invoice_pet_name and policy_pet_name:
        if invoice_pet_name != policy_pet_name:
            # Check for common variations (Max vs Maximus, etc.)
            if not (invoice_pet_name in policy_pet_name or policy_pet_name in invoice_pet_name):
                issues.append({
                    "type": "pet_name_mismatch",
                    "severity": "error",
                    "message": f"Invoice pet name '{invoice.get('pet_name')}' doesn't match policy pet '{pet.get('name')}'",
                    "invoice_value": invoice.get("pet_name"),
                    "policy_value": pet.get("name")
                })
            else:
                warnings.append({
                    "type": "pet_name_variation",
                    "severity": "info",
                    "message": f"Pet name variation detected: '{invoice.get('pet_name')}' vs '{pet.get('name')}'",
                })

    # Check 2: Date consistency
    invoice_date = invoice.get("date", request.service_date)
    record_date = medical_records.get("visit_date", "")

    if invoice_date and record_date and invoice_date != record_date:
        issues.append({
            "type": "date_mismatch",
            "severity": "warning",
            "message": f"Invoice date '{invoice_date}' differs from medical record date '{record_date}'",
            "invoice_value": invoice_date,
            "record_value": record_date
        })

    # Check 3: Amount consistency
    invoice_amount = invoice.get("amount", request.claim_amount)
    record_amount = medical_records.get("total_charges")

    if invoice_amount and record_amount:
        if abs(invoice_amount - record_amount) > 1:  # Allow $1 rounding difference
            issues.append({
                "type": "amount_mismatch",
                "severity": "error",
                "message": f"Invoice amount ${invoice_amount} differs from records ${record_amount}",
                "invoice_value": invoice_amount,
                "record_value": record_amount,
                "difference": abs(invoice_amount - record_amount)
            })

    # Check 4: Procedure consistency
    invoice_procedures = set(p.lower() for p in invoice.get("procedures", []))
    record_procedures = set(p.lower() for p in medical_records.get("procedures_performed", []))

    if invoice_procedures and record_procedures:
        invoice_only = invoice_procedures - record_procedures
        records_only = record_procedures - invoice_procedures

        if invoice_only:
            issues.append({
                "type": "procedure_on_invoice_only",
                "severity": "warning",
                "message": f"Procedures on invoice but not in medical records: {list(invoice_only)}",
                "invoice_only": list(invoice_only)
            })

        if records_only:
            warnings.append({
                "type": "procedure_in_records_only",
                "severity": "info",
                "message": f"Procedures in records but not on invoice: {list(records_only)}",
                "records_only": list(records_only)
            })

    # Check 5: Diagnosis consistency
    invoice_diagnosis = (invoice.get("diagnosis") or "").lower()
    record_diagnosis = (medical_records.get("diagnosis") or "").lower()
    claim_diagnosis = (request.diagnosis_description or "").lower()

    diagnoses = [d for d in [invoice_diagnosis, record_diagnosis, claim_diagnosis] if d]
    if len(diagnoses) >= 2:
        # Simple similarity check - in production would use NLP
        if len(set(diagnoses)) > 1:
            # Check if they're semantically similar
            all_similar = all(
                any(word in d2 for word in d1.split())
                for d1, d2 in [(diagnoses[0], diagnoses[1])]
            )
            if not all_similar:
                issues.append({
                    "type": "diagnosis_mismatch",
                    "severity": "warning",
                    "message": "Diagnosis descriptions differ across documents",
                    "values": diagnoses
                })

    # Calculate score
    score = 100
    for issue in issues:
        if issue["severity"] == "error":
            score -= 25
        elif issue["severity"] == "warning":
            score -= 10
    for warning in warnings:
        score -= 3

    score = max(0, score)

    return {
        "validation_type": "document_consistency",
        "passed": len([i for i in issues if i["severity"] == "error"]) == 0,
        "score": score,
        "documents_compared": {
            "invoice_provided": bool(request.invoice_data),
            "medical_records_provided": bool(request.medical_record_data)
        },
        "issues": issues,
        "warnings": warnings,
        "recommendation": "Request document clarification" if score < 70 else "Documents consistent"
    }


# =============================================================================
# ENDPOINT 3: Claim Completeness & Sequence
# =============================================================================

@router.post("/completeness-sequence")
async def validate_completeness_sequence(request: ClaimValidationRequest) -> Dict[str, Any]:
    """
    Validate clinical workflow completeness and logical sequence.
    AI catches missing prerequisites and illogical sequences.

    LLM Tool: validate_claim_sequence(claim_data)
    """
    issues = []
    warnings = []

    procedures = request.procedure_codes or []

    # Get historical claims for this pet
    store = get_data_store()
    pet_claims = store.get_claims_by_pet(request.pet_id) if request.pet_id else []

    # Sort by date
    pet_claims.sort(key=lambda x: x.get("service_date", ""), reverse=True)
    recent_claims = pet_claims[:10]  # Last 10 claims

    # Check each procedure for prerequisites
    for proc_code in procedures:
        sequence_info = PROCEDURE_SEQUENCES.get(proc_code)

        if sequence_info:
            required_before = sequence_info["required_before"]
            required_before_names = sequence_info["required_before_names"]

            # Check if prerequisites exist in recent claims or current claim
            all_procedures = set(procedures)
            for claim in recent_claims:
                claim_procs = claim.get("procedure_codes", [])
                if isinstance(claim_procs, list):
                    all_procedures.update(claim_procs)

            missing_prereqs = []
            for i, prereq in enumerate(required_before):
                if prereq not in all_procedures:
                    # Check by name in descriptions
                    prereq_name = required_before_names[i]
                    found_by_name = any(
                        prereq_name.lower() in (desc or "").lower()
                        for desc in request.procedure_descriptions
                    )
                    if not found_by_name:
                        missing_prereqs.append(prereq_name)

            if missing_prereqs:
                issues.append({
                    "type": "missing_prerequisite",
                    "severity": "warning",
                    "message": f"{sequence_info['name']} typically requires: {', '.join(missing_prereqs)}",
                    "procedure": sequence_info["name"],
                    "missing": missing_prereqs
                })

            # Check for required follow-ups (flag as informational)
            required_after = sequence_info.get("required_after_names", [])
            if required_after:
                warnings.append({
                    "type": "follow_up_expected",
                    "severity": "info",
                    "message": f"After {sequence_info['name']}, expect: {', '.join(required_after)}",
                    "expected_follow_ups": required_after
                })

    # Check for logical sequence issues
    # Surgery without anesthesia
    surgery_codes = [p for p in procedures if p.startswith("SURG")]
    anesthesia_codes = [p for p in procedures if "ANEST" in p or "SED" in p]

    if surgery_codes and not anesthesia_codes:
        # Check descriptions
        has_anesthesia = any(
            "anesthesia" in (desc or "").lower() or "sedation" in (desc or "").lower()
            for desc in request.procedure_descriptions
        )
        if not has_anesthesia:
            issues.append({
                "type": "missing_anesthesia",
                "severity": "warning",
                "message": "Surgery procedures found without anesthesia/sedation billing",
                "surgeries": surgery_codes
            })

    # Check diagnosis-specific completeness
    diagnosis_info = DIAGNOSIS_TREATMENT_MAP.get(request.diagnosis_code)
    if diagnosis_info:
        required_diagnostics = diagnosis_info.get("required_diagnostics", [])
        missing_diagnostics = []

        all_proc_text = " ".join(request.procedure_descriptions).lower()
        for diag in required_diagnostics:
            if diag.lower() not in all_proc_text:
                missing_diagnostics.append(diag)

        if missing_diagnostics:
            warnings.append({
                "type": "missing_diagnostics",
                "severity": "info",
                "message": f"Typical diagnostics for {diagnosis_info['description']} not found: {', '.join(missing_diagnostics)}",
                "expected": required_diagnostics,
                "missing": missing_diagnostics
            })

    # Calculate completeness score
    score = 100
    for issue in issues:
        if issue["severity"] == "error":
            score -= 25
        elif issue["severity"] == "warning":
            score -= 10

    score = max(0, score)

    return {
        "validation_type": "completeness_sequence",
        "passed": len([i for i in issues if i["severity"] == "error"]) == 0,
        "score": score,
        "procedures_checked": len(procedures),
        "historical_claims_reviewed": len(recent_claims),
        "issues": issues,
        "warnings": warnings,
        "recommendation": "Review clinical workflow" if score < 80 else "Sequence appears complete"
    }


# =============================================================================
# ENDPOINT 4: License Verification (Regulatory)
# =============================================================================

@router.post("/license-verification")
async def validate_license(request: ClaimValidationRequest) -> Dict[str, Any]:
    """
    Verify veterinary provider licensing compliance.

    LLM Tool: verify_provider_license(provider_id, service_date)
    """
    issues = []
    warnings = []

    store = get_data_store()
    provider = store.get_provider(request.provider_id)

    if not provider:
        return {
            "validation_type": "license_verification",
            "passed": False,
            "score": 0,
            "issues": [{"type": "provider_not_found", "severity": "critical", "message": f"Provider {request.provider_id} not found"}],
            "warnings": []
        }

    # Check license status
    license_status = provider.get("license_status", "active")
    license_expiry = provider.get("license_expiry_date")
    license_state = provider.get("license_state", "")
    dea_number = provider.get("dea_number")
    facility_license = provider.get("facility_license")

    # Check 1: License status
    if license_status != "active":
        issues.append({
            "type": "inactive_license",
            "severity": "critical",
            "message": f"Provider license status is '{license_status}'",
            "license_status": license_status
        })

    # Check 2: License expiry
    if license_expiry:
        try:
            expiry_date = datetime.fromisoformat(license_expiry)
            service_date = datetime.fromisoformat(request.service_date)

            if expiry_date < service_date:
                issues.append({
                    "type": "expired_license",
                    "severity": "critical",
                    "message": f"License expired on {license_expiry}, service provided on {request.service_date}",
                    "expiry_date": license_expiry,
                    "service_date": request.service_date
                })
            elif expiry_date < datetime.now() + timedelta(days=30):
                warnings.append({
                    "type": "license_expiring_soon",
                    "severity": "info",
                    "message": f"Provider license expires on {license_expiry}",
                    "expiry_date": license_expiry
                })
        except (ValueError, TypeError):
            warnings.append({
                "type": "invalid_expiry_date",
                "severity": "warning",
                "message": f"Could not parse license expiry date: {license_expiry}"
            })

    # Check 3: State requirements
    state_reqs = STATE_REQUIREMENTS.get(license_state)
    if state_reqs:
        # Check facility license if required
        if state_reqs["requires_facility_license"] and not facility_license:
            issues.append({
                "type": "missing_facility_license",
                "severity": "warning",
                "message": f"State {license_state} requires facility license - not found",
                "state": license_state
            })

        # Check DEA for controlled substance states
        if state_reqs["controlled_substance_state_license"] and not dea_number:
            warnings.append({
                "type": "missing_dea",
                "severity": "info",
                "message": "DEA number not on file - required if controlled substances prescribed",
                "state": license_state
            })

    # Check 4: Verify license format matches state
    license_number = provider.get("license_number", "")
    if state_reqs and license_number:
        expected_prefix = state_reqs.get("license_prefix", "")
        if expected_prefix and not license_number.startswith(expected_prefix):
            warnings.append({
                "type": "license_format_warning",
                "severity": "info",
                "message": f"License number format may not match {license_state} standard (expected prefix: {expected_prefix})",
                "license_number": license_number
            })

    # Calculate score
    score = 100
    for issue in issues:
        if issue["severity"] == "critical":
            score -= 50
        elif issue["severity"] == "warning":
            score -= 15
    for warning in warnings:
        score -= 5

    score = max(0, score)

    return {
        "validation_type": "license_verification",
        "passed": len([i for i in issues if i["severity"] == "critical"]) == 0,
        "score": score,
        "provider_id": request.provider_id,
        "provider_name": provider.get("name"),
        "license_details": {
            "license_number": license_number,
            "license_state": license_state,
            "license_status": license_status,
            "license_expiry": license_expiry,
            "dea_number": dea_number,
            "facility_license": facility_license
        },
        "issues": issues,
        "warnings": warnings,
        "recommendation": "Do not process - licensing issue" if score < 50 else "License verification passed"
    }


# =============================================================================
# ENDPOINT 5: Controlled Substance Compliance (Regulatory)
# =============================================================================

@router.post("/controlled-substance")
async def validate_controlled_substances(request: ClaimValidationRequest) -> Dict[str, Any]:
    """
    Validate controlled substance prescriptions for compliance.

    LLM Tool: validate_controlled_substances(claim_data)
    """
    issues = []
    warnings = []
    controlled_found = []

    medications = request.medications or []

    # Check each medication
    for med in medications:
        med_lower = med.lower()

        for drug_name, drug_info in CONTROLLED_SUBSTANCES.items():
            if drug_name.lower() in med_lower:
                controlled_found.append({
                    "medication": med,
                    "controlled_name": drug_name,
                    "schedule": drug_info["schedule"]
                })

                # Check DEA requirement
                if drug_info["requires_dea"]:
                    # Verify provider has DEA
                    store = get_data_store()
                    provider = store.get_provider(request.provider_id)

                    if provider and not provider.get("dea_number"):
                        issues.append({
                            "type": "missing_dea_for_controlled",
                            "severity": "error",
                            "message": f"{drug_name} (Schedule {drug_info['schedule']}) requires DEA registration - not found for provider",
                            "medication": drug_name,
                            "schedule": drug_info["schedule"]
                        })

                # Check diagnosis appropriateness
                if drug_info["requires_diagnosis"]:
                    common_diagnoses = drug_info["common_diagnoses"]
                    diagnosis_match = any(
                        diag.lower() in request.diagnosis_code.lower() or
                        diag.lower() in (request.diagnosis_description or "").lower()
                        for diag in common_diagnoses
                    )

                    if not diagnosis_match:
                        issues.append({
                            "type": "unusual_diagnosis_for_controlled",
                            "severity": "warning",
                            "message": f"{drug_name} typically prescribed for {common_diagnoses}, current diagnosis: {request.diagnosis_code}",
                            "medication": drug_name,
                            "typical_diagnoses": common_diagnoses,
                            "current_diagnosis": request.diagnosis_code
                        })

                # Documentation requirements
                required_docs = drug_info["documentation_required"]
                warnings.append({
                    "type": "documentation_reminder",
                    "severity": "info",
                    "message": f"{drug_name} requires documentation: {', '.join(required_docs)}",
                    "medication": drug_name,
                    "required_documentation": required_docs
                })

    # Calculate score
    score = 100
    for issue in issues:
        if issue["severity"] == "error":
            score -= 30
        elif issue["severity"] == "warning":
            score -= 10

    score = max(0, score)

    return {
        "validation_type": "controlled_substance_compliance",
        "passed": len([i for i in issues if i["severity"] == "error"]) == 0,
        "score": score,
        "controlled_substances_found": controlled_found,
        "total_medications_checked": len(medications),
        "issues": issues,
        "warnings": warnings,
        "recommendation": "Compliance review required" if score < 70 else "Controlled substance documentation adequate"
    }


# =============================================================================
# ENDPOINT 6: Comprehensive Validation (All Checks)
# =============================================================================

@router.post("/comprehensive")
async def validate_comprehensive(request: ClaimValidationRequest) -> Dict[str, Any]:
    """
    Run all validation checks and return comprehensive data quality score.

    LLM Tool: validate_claim_comprehensive(claim_data)
    """
    results = {}

    # Run all validations
    results["diagnosis_treatment"] = await validate_diagnosis_treatment(request)
    results["document_consistency"] = await validate_document_consistency(request)
    results["completeness_sequence"] = await validate_completeness_sequence(request)
    results["license_verification"] = await validate_license(request)
    results["controlled_substance"] = await validate_controlled_substances(request)

    # Aggregate scores
    scores = [r["score"] for r in results.values()]
    overall_score = sum(scores) / len(scores) if scores else 0

    # Aggregate all issues
    all_issues = []
    all_warnings = []

    for check_name, result in results.items():
        for issue in result.get("issues", []):
            issue["source"] = check_name
            all_issues.append(issue)
        for warning in result.get("warnings", []):
            warning["source"] = check_name
            all_warnings.append(warning)

    # Sort by severity
    severity_order = {"critical": 0, "error": 1, "warning": 2, "info": 3}
    all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 99))

    # Determine overall pass/fail
    critical_issues = [i for i in all_issues if i.get("severity") == "critical"]
    error_issues = [i for i in all_issues if i.get("severity") == "error"]

    passed = len(critical_issues) == 0 and len(error_issues) <= 1

    # Generate recommendation
    if overall_score >= 90:
        recommendation = "AUTO_PROCESS - High data quality"
    elif overall_score >= 70:
        recommendation = "STANDARD_REVIEW - Minor issues detected"
    elif overall_score >= 50:
        recommendation = "MANUAL_REVIEW - Multiple data quality issues"
    else:
        recommendation = "HOLD_FOR_REVIEW - Significant data quality concerns"

    return {
        "validation_type": "comprehensive",
        "passed": passed,
        "overall_score": round(overall_score, 1),
        "individual_scores": {
            "diagnosis_treatment": results["diagnosis_treatment"]["score"],
            "document_consistency": results["document_consistency"]["score"],
            "completeness_sequence": results["completeness_sequence"]["score"],
            "license_verification": results["license_verification"]["score"],
            "controlled_substance": results["controlled_substance"]["score"]
        },
        "summary": {
            "critical_issues": len(critical_issues),
            "errors": len(error_issues),
            "warnings": len([i for i in all_issues if i.get("severity") == "warning"]),
            "info": len(all_warnings)
        },
        "issues": all_issues,
        "warnings": all_warnings,
        "recommendation": recommendation,
        "detailed_results": results
    }


# =============================================================================
# ENDPOINT 7: Get Validation Reference Data
# =============================================================================

@router.get("/reference/diagnosis-treatments")
async def get_diagnosis_treatment_reference() -> Dict[str, Any]:
    """Get reference data for diagnosis-treatment mappings."""
    return {
        "count": len(DIAGNOSIS_TREATMENT_MAP),
        "mappings": DIAGNOSIS_TREATMENT_MAP
    }


@router.get("/reference/procedure-sequences")
async def get_procedure_sequence_reference() -> Dict[str, Any]:
    """Get reference data for procedure sequences."""
    return {
        "count": len(PROCEDURE_SEQUENCES),
        "sequences": PROCEDURE_SEQUENCES
    }


@router.get("/reference/controlled-substances")
async def get_controlled_substance_reference() -> Dict[str, Any]:
    """Get reference data for controlled substances."""
    return {
        "count": len(CONTROLLED_SUBSTANCES),
        "substances": CONTROLLED_SUBSTANCES
    }


@router.get("/reference/state-requirements")
async def get_state_requirements_reference() -> Dict[str, Any]:
    """Get reference data for state licensing requirements."""
    return {
        "count": len(STATE_REQUIREMENTS),
        "states": STATE_REQUIREMENTS
    }


@router.get("/scenarios")
async def get_validation_scenarios() -> Dict[str, Any]:
    """
    Get validation test scenarios for demo purposes.
    Each scenario demonstrates a specific data quality issue.
    """
    import json
    import os

    scenarios_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data", "validation_scenarios.json"
    )

    try:
        with open(scenarios_path, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {"error": "Scenarios file not found", "scenarios": []}


@router.post("/scenarios/{scenario_id}/run")
async def run_validation_scenario(scenario_id: str) -> Dict[str, Any]:
    """
    Run a specific validation scenario and return results.
    """
    import json
    import os

    scenarios_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data", "validation_scenarios.json"
    )

    try:
        with open(scenarios_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"error": "Scenarios file not found"}

    # Find the scenario
    scenario = None
    for s in data.get("validation_scenarios", []):
        if s["scenario_id"] == scenario_id:
            scenario = s
            break

    if not scenario:
        return {"error": f"Scenario {scenario_id} not found"}

    # Build request from scenario data
    claim_data = scenario["claim_data"]
    request = ClaimValidationRequest(**claim_data)

    # Run the appropriate validation
    validation_type = scenario["validation_type"]

    if validation_type == "diagnosis_treatment_mismatch":
        result = await validate_diagnosis_treatment(request)
    elif validation_type == "document_consistency":
        result = await validate_document_consistency(request)
    elif validation_type == "completeness_sequence":
        result = await validate_completeness_sequence(request)
    elif validation_type == "license_verification":
        result = await validate_license(request)
    elif validation_type == "controlled_substance":
        result = await validate_controlled_substances(request)
    elif validation_type == "comprehensive":
        result = await validate_comprehensive(request)
    else:
        return {"error": f"Unknown validation type: {validation_type}"}

    return {
        "scenario": scenario,
        "expected_result": scenario["expected_result"],
        "actual_result": result,
        "match": _check_result_match(scenario["expected_result"], result)
    }


def _check_result_match(expected: str, result: Dict) -> bool:
    """Check if validation result matches expected outcome."""
    if expected == "FAIL":
        return not result.get("passed", True)
    elif expected == "WARNING":
        return result.get("passed", False) and len(result.get("issues", [])) > 0
    elif expected == "CRITICAL":
        critical = [i for i in result.get("issues", []) if i.get("severity") == "critical"]
        return len(critical) > 0
    elif expected == "MANUAL_REVIEW":
        return result.get("score", 100) < 70
    return True
