"""
DocGen Agent - AI-Driven Document Processing Agent

This is the MAIN agent that controls the entire document processing flow.
The agent receives context (existing claims, policy info) and a new document,
then uses tools to: check duplicates, extract data, validate, and submit claims.

The agent THINKS and DECIDES - it's not just a function wrapper.
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# SYSTEM PROMPT - This guides the agent's behavior
# =============================================================================

DOCGEN_AGENT_SYSTEM_PROMPT = """You are a STRICT Pet Insurance Claims Processing Agent. Your job is to PROTECT against fraud while processing legitimate claims.

## YOUR ROLE
You are a specialized agent for processing veterinary invoices, lab results, prescriptions, and medical documents for pet insurance claims. You must be VIGILANT and SKEPTICAL - assume every submission could be fraudulent until proven otherwise.

## PET INSURANCE DOMAIN KNOWLEDGE
You understand:
- Veterinary terminology and common procedures
- Lab result formats (blood work, urinalysis, x-rays, etc.)
- Common pet conditions and treatments
- Typical costs for veterinary services
- Fraud patterns in pet insurance (duplicate submissions, inflated bills, phantom services)

## CONTEXT YOU RECEIVE
- Customer/Policy information (deductible, coverage %, limits)
- Existing claims/invoices already submitted for this policy
- The new document content to process

## YOUR TOOLS
1. **check_duplicate** - Check for exact or near-duplicate submissions
2. **extract_document** - Extract structured data from document
3. **validate_claim** - Validate against business rules
4. **calculate_billing** - Calculate reimbursement
5. **submit_claim** - Submit for processing (only if fully validated)

## CRITICAL: FRAUD DETECTION RULES

### EXACT DUPLICATES (REJECT IMMEDIATELY):
- Same invoice number
- Same document content hash
- Same provider + same date + same amount

### SUSPICIOUS MATCHES (FLAG FOR MANUAL REVIEW):
You MUST flag for manual_review if ANY of these are true:
- Invoice numbers are SIMILAR (e.g., INV-1234 vs INV-12345, LAB-2024-5678 vs LAB-2024-567811)
- Same provider + same patient + dates within 7 days
- Same provider + amount within 10% + dates within 30 days
- Multiple submissions from same provider in short timeframe
- Total amount matches previous claim exactly
- Patient name/pet name matches with different invoice
- Line items are 80%+ similar to existing claim

### RED FLAGS (FLAG FOR INVESTIGATION):
- Future service dates
- Round number amounts ($100, $500, $1000 exactly)
- Weekend/holiday service dates for non-emergency
- Unusual service combinations
- Amount exceeds typical range for service type

## DECISION OPTIONS
- **proceed**: Only for clearly unique, valid claims with NO suspicious patterns
- **duplicate_rejected**: Exact duplicate - reject immediately
- **needs_review**: ANY suspicious pattern detected - MUST use this for similar invoices
- **investigation**: Multiple red flags - potential fraud

## DECISION FLOW
1. COMPARE against ALL existing claims - look for ANY similarity
2. If >60% field match with existing claim → needs_review
3. If invoice number is similar (not exact) → needs_review
4. If same provider + close dates → needs_review
5. Only proceed if document is clearly UNIQUE and VALID

## BE STRICT
- When in doubt, flag for review
- Similar is NOT the same as different
- Protect the insurance company from fraud
- One extra review is better than one fraudulent payout

## OUTPUT FORMAT
Always respond with JSON containing:
{
    "thinking": "Your step-by-step reasoning...",
    "decision": "proceed|duplicate_rejected|needs_review|error",
    "confidence": 0.95,
    "explanation": "Human-readable explanation formatted with bullet points",
    "extracted_data": {
        "invoice_number": "INV-12345",
        "provider_name": "Happy Paws Veterinary Clinic",
        "provider_address": "123 Main St",
        "patient_name": "Buddy",
        "patient_species": "Dog",
        "service_date": "2024-01-15",
        "total_amount": 150.00,
        "diagnosis": "Annual checkup",
        "line_items": [...]
    },
    "billing_info": {
        "claim_amount": 150.00,
        "deductible_applied": 50.00,
        "amount_after_deductible": 100.00,
        "reimbursement_rate": 0.8,
        "final_payout": 80.00,
        "customer_responsibility": 70.00
    }
}

CRITICAL: You MUST include "extracted_data" with all claim fields you extracted from the document.
This data is stored and used to detect duplicates in future submissions.

## FORMATTING REQUIREMENTS FOR EXPLANATION
The "explanation" field will be shown to users. Format it clearly with:
- Use bullet points (•) for each step
- Put each major point on a new line
- Keep it concise but informative

Example good format:
"explanation": "• Verified document is not a duplicate\\n• Extracted provider: Happy Paws Clinic\\n• Service date: 2024-01-15\\n• Total amount: $150.00\\n• Claim approved for reimbursement"

DO NOT use long run-on sentences. Break into clear bullet points.

## IMPORTANT
- ALWAYS check for duplicates FIRST before any other processing
- EXPLAIN your reasoning clearly
- Be conservative - when in doubt, flag for review
- Protect against fraud while being fair to legitimate claims
"""


# =============================================================================
# TOOL DEFINITIONS for Claude
# =============================================================================

AGENT_TOOLS = [
    {
        "name": "check_duplicate",
        "description": "Check if the current document is a duplicate of any previously submitted document. Compares invoice numbers, provider+date+amount combinations, and content similarity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "invoice_number": {
                    "type": "string",
                    "description": "Invoice/receipt number from the current document"
                },
                "provider_name": {
                    "type": "string",
                    "description": "Provider/clinic name from the current document"
                },
                "service_date": {
                    "type": "string",
                    "description": "Service date in YYYY-MM-DD format"
                },
                "total_amount": {
                    "type": "number",
                    "description": "Total amount from the document"
                },
                "document_hash": {
                    "type": "string",
                    "description": "Hash of document content for exact match detection"
                }
            },
            "required": ["provider_name"]
        }
    },
    {
        "name": "extract_document",
        "description": "Extract structured data from the document content. Parses provider info, patient info, services, line items, and financial totals.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_content": {
                    "type": "string",
                    "description": "The raw text content of the document"
                },
                "document_type_hint": {
                    "type": "string",
                    "enum": ["invoice", "receipt", "lab_results", "prescription", "unknown"],
                    "description": "Hint about the document type"
                }
            },
            "required": ["document_content"]
        }
    },
    {
        "name": "validate_claim",
        "description": "Validate the extracted claim data against business rules and policy terms.",
        "input_schema": {
            "type": "object",
            "properties": {
                "claim_data": {
                    "type": "object",
                    "description": "The extracted claim data to validate"
                },
                "policy_info": {
                    "type": "object",
                    "description": "Policy information for validation"
                }
            },
            "required": ["claim_data"]
        }
    },
    {
        "name": "calculate_billing",
        "description": "Calculate reimbursement amounts based on policy terms (deductible, co-pay, limits).",
        "input_schema": {
            "type": "object",
            "properties": {
                "claim_amount": {
                    "type": "number",
                    "description": "Total claim amount"
                },
                "policy_deductible": {
                    "type": "number",
                    "description": "Annual deductible amount"
                },
                "deductible_met": {
                    "type": "number",
                    "description": "Amount of deductible already met this year"
                },
                "reimbursement_rate": {
                    "type": "number",
                    "description": "Reimbursement percentage (e.g., 0.8 for 80%)"
                },
                "annual_limit": {
                    "type": "number",
                    "description": "Annual coverage limit"
                },
                "used_limit": {
                    "type": "number",
                    "description": "Amount already used from annual limit"
                }
            },
            "required": ["claim_amount"]
        }
    },
    {
        "name": "submit_claim",
        "description": "Submit the validated claim for processing. Only call this after successful validation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "claim_data": {
                    "type": "object",
                    "description": "Complete claim data to submit"
                },
                "billing_info": {
                    "type": "object",
                    "description": "Calculated billing information"
                },
                "agent_decision": {
                    "type": "string",
                    "enum": ["auto_approve", "standard_review", "manual_review"],
                    "description": "Agent's recommended decision"
                },
                "agent_reasoning": {
                    "type": "string",
                    "description": "Agent's explanation for the decision"
                }
            },
            "required": ["claim_data", "agent_decision", "agent_reasoning"]
        }
    }
]


# =============================================================================
# TOOL IMPLEMENTATIONS
# =============================================================================

class AgentTools:
    """Implementation of tools available to the DocGen Agent."""

    def __init__(self, context: Dict[str, Any]):
        """
        Initialize with context.

        Args:
            context: Contains existing_claims, policy_info, fingerprints, etc.
        """
        self.context = context
        self.existing_claims = context.get("existing_claims", [])
        self.fingerprints = context.get("fingerprints", {})
        self.policy_info = context.get("policy_info", {})

    async def check_duplicate(
        self,
        invoice_number: Optional[str] = None,
        provider_name: Optional[str] = None,
        service_date: Optional[str] = None,
        total_amount: Optional[float] = None,
        document_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Check if document is a duplicate."""

        duplicates_found = []

        # Check 1: Exact content hash match
        if document_hash and document_hash in self.fingerprints:
            existing = self.fingerprints[document_hash]
            duplicates_found.append({
                "match_type": "exact_content",
                "confidence": 100,
                "reason": f"Identical document content. Previously submitted as '{existing.get('filename')}' in batch {existing.get('batch_id', 'unknown')[:8]}...",
                "original_submission": existing
            })

        # Check 2: Invoice number match
        if invoice_number:
            for claim in self.existing_claims:
                if claim.get("invoice_number", "").lower() == invoice_number.lower():
                    duplicates_found.append({
                        "match_type": "invoice_number",
                        "confidence": 95,
                        "reason": f"Invoice #{invoice_number} was already submitted on {claim.get('submission_date', 'unknown')}",
                        "original_submission": claim
                    })

        # Check 3: Provider + Date + Amount match
        if provider_name and service_date and total_amount:
            for claim in self.existing_claims:
                if (claim.get("provider_name", "").lower() == provider_name.lower() and
                    claim.get("service_date") == service_date and
                    abs(float(claim.get("total_amount", 0)) - total_amount) < 0.01):
                    duplicates_found.append({
                        "match_type": "provider_date_amount",
                        "confidence": 90,
                        "reason": f"Same provider ({provider_name}), date ({service_date}), and amount (${total_amount:.2f}) as previous submission",
                        "original_submission": claim
                    })

        if duplicates_found:
            # Return highest confidence match
            best_match = max(duplicates_found, key=lambda x: x["confidence"])
            return {
                "is_duplicate": True,
                "confidence": best_match["confidence"],
                "match_type": best_match["match_type"],
                "reason": best_match["reason"],
                "original_submission": best_match.get("original_submission"),
                "all_matches": duplicates_found
            }

        return {
            "is_duplicate": False,
            "confidence": 100,
            "reason": "No matching documents found in submission history",
            "checks_performed": ["content_hash", "invoice_number", "provider_date_amount"]
        }

    async def extract_document(
        self,
        document_content: str,
        document_type_hint: str = "unknown"
    ) -> Dict[str, Any]:
        """Extract structured data from document."""
        # This is handled by the agent itself through its reasoning
        # The tool just validates the extraction format
        return {
            "status": "extraction_delegated_to_agent",
            "hint": document_type_hint
        }

    async def validate_claim(
        self,
        claim_data: Dict[str, Any],
        policy_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Validate claim against business rules."""
        issues = []
        warnings = []

        policy = policy_info or self.policy_info

        # Required fields check
        required = ["service_date", "provider_name", "total_amount"]
        for field in required:
            if not claim_data.get(field):
                issues.append({
                    "code": "MISSING_REQUIRED",
                    "field": field,
                    "message": f"Required field '{field}' is missing"
                })

        # Date validation
        service_date = claim_data.get("service_date")
        if service_date:
            try:
                svc_date = datetime.fromisoformat(service_date.replace("Z", "+00:00"))
                if svc_date.date() > datetime.utcnow().date():
                    issues.append({
                        "code": "FUTURE_DATE",
                        "field": "service_date",
                        "message": "Service date cannot be in the future"
                    })
                elif (datetime.utcnow() - svc_date).days > 365:
                    warnings.append({
                        "code": "OLD_DATE",
                        "field": "service_date",
                        "message": "Service date is more than 1 year ago"
                    })
            except:
                issues.append({
                    "code": "INVALID_DATE",
                    "field": "service_date",
                    "message": "Invalid date format"
                })

        # Amount validation
        amount = claim_data.get("total_amount", 0)
        if amount <= 0:
            issues.append({
                "code": "INVALID_AMOUNT",
                "field": "total_amount",
                "message": "Claim amount must be greater than zero"
            })
        elif amount > 50000:
            warnings.append({
                "code": "HIGH_AMOUNT",
                "field": "total_amount",
                "message": f"Unusually high claim amount: ${amount:,.2f}"
            })

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "validation_timestamp": datetime.utcnow().isoformat()
        }

    async def calculate_billing(
        self,
        claim_amount: float,
        policy_deductible: float = 500,
        deductible_met: float = 0,
        reimbursement_rate: float = 0.8,
        annual_limit: float = 10000,
        used_limit: float = 0
    ) -> Dict[str, Any]:
        """Calculate reimbursement."""

        # Apply deductible
        remaining_deductible = max(0, policy_deductible - deductible_met)
        deductible_applied = min(claim_amount, remaining_deductible)
        after_deductible = claim_amount - deductible_applied

        # Apply reimbursement rate
        reimbursement = after_deductible * reimbursement_rate

        # Apply annual limit
        remaining_limit = max(0, annual_limit - used_limit)
        final_payout = min(reimbursement, remaining_limit)

        return {
            "claim_amount": claim_amount,
            "deductible_applied": deductible_applied,
            "amount_after_deductible": after_deductible,
            "reimbursement_rate": reimbursement_rate,
            "reimbursement_amount": reimbursement,
            "annual_limit_remaining": remaining_limit,
            "final_payout": final_payout,
            "customer_responsibility": claim_amount - final_payout,
            "calculation_breakdown": (
                f"${claim_amount:.2f} - ${deductible_applied:.2f} (deductible) = ${after_deductible:.2f} "
                f"× {reimbursement_rate*100:.0f}% = ${reimbursement:.2f} → Final: ${final_payout:.2f}"
            )
        }

    async def submit_claim(
        self,
        claim_data: Dict[str, Any],
        billing_info: Optional[Dict[str, Any]] = None,
        agent_decision: str = "standard_review",
        agent_reasoning: str = ""
    ) -> Dict[str, Any]:
        """Submit the claim to PetInsure360 backend."""
        import httpx
        import os

        # PetInsure360 backend URL
        petinsure_url = os.getenv("PETINSURE_BACKEND_URL", "http://localhost:3002")

        # Prepare claim submission data
        submit_data = {
            "scenario_id": claim_data.get("scenario_id", "DOCGEN-UPLOAD"),
            "customer_id": self.batch.claim_data.get("customer_id") if self.batch and self.batch.claim_data else claim_data.get("customer_id", "UNKNOWN"),
            "pet_id": self.batch.claim_data.get("pet_id") if self.batch and self.batch.claim_data else claim_data.get("pet_id", "UNKNOWN"),
            "policy_id": self.batch.policy_number if self.batch else claim_data.get("policy_id"),
            "claim_type": claim_data.get("claim_type", "Illness"),
            "claim_category": claim_data.get("diagnosis", "General"),
            "diagnosis_code": claim_data.get("diagnosis_code", ""),
            "diagnosis": claim_data.get("diagnosis", ""),
            "service_date": claim_data.get("service_date", datetime.utcnow().date().isoformat()),
            "treatment_notes": claim_data.get("treatment_notes", agent_reasoning),
            "line_items": claim_data.get("line_items", []),
            "claim_amount": claim_data.get("total_amount", 0),
            "provider_id": claim_data.get("provider_id", ""),
            "provider_name": claim_data.get("provider_name", ""),
            "is_in_network": claim_data.get("is_in_network", True),
            "is_emergency": claim_data.get("is_emergency", False)
        }

        # Try to submit to PetInsure360 backend
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{petinsure_url}/api/pipeline/submit-claim",
                    json=submit_data
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Claim created in PetInsure360: {result.get('claim_number')}")
                    return {
                        "claim_id": result.get("claim_id"),
                        "claim_number": result.get("claim_number"),
                        "status": "submitted",
                        "decision": agent_decision,
                        "reasoning": agent_reasoning,
                        "submitted_at": datetime.utcnow().isoformat(),
                        "claim_data": claim_data,
                        "billing_info": billing_info,
                        "petinsure_response": result
                    }
                else:
                    logger.warning(f"Failed to create claim in PetInsure360: {response.status_code} - {response.text}")
        except Exception as e:
            logger.warning(f"Could not connect to PetInsure360 backend: {e}")

        # Fallback: generate local claim ID if backend unavailable
        claim_id = f"CLM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{hash(str(claim_data)) % 10000:04X}"

        return {
            "claim_id": claim_id,
            "status": "submitted_local",
            "decision": agent_decision,
            "reasoning": agent_reasoning,
            "submitted_at": datetime.utcnow().isoformat(),
            "claim_data": claim_data,
            "billing_info": billing_info
        }

    async def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name."""
        tool_map = {
            "check_duplicate": self.check_duplicate,
            "extract_document": self.extract_document,
            "validate_claim": self.validate_claim,
            "calculate_billing": self.calculate_billing,
            "submit_claim": self.submit_claim
        }

        if tool_name not in tool_map:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            result = await tool_map[tool_name](**tool_input)
            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {"error": str(e)}


# =============================================================================
# DOCGEN AGENT
# =============================================================================

class DocGenAgent:
    """
    The main AI Agent for document processing.

    This agent THINKS and DECIDES. It's not just a function wrapper.
    It receives context, reasons about the document, and uses tools.
    """

    def __init__(self):
        if settings.AI_PROVIDER == "claude" and settings.ANTHROPIC_API_KEY:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.model = settings.CLAUDE_MODEL
        else:
            raise ValueError("Claude API required for agent-driven processing")

    async def process_document(
        self,
        document_content: str,
        document_filename: str,
        document_hash: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a document using agent reasoning.

        Args:
            document_content: The text content of the document
            document_filename: Original filename
            document_hash: SHA-256 hash of content
            context: Contains existing_claims, policy_info, fingerprints

        Returns:
            Agent's decision and processing results
        """
        logger.info(f"DocGen Agent processing: {document_filename}")

        # Initialize tools with context
        tools = AgentTools(context)

        # Build the user message with context
        user_message = self._build_user_message(
            document_content, document_filename, document_hash, context
        )

        # Run agent loop
        messages = [{"role": "user", "content": user_message}]
        final_result = None
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Agent iteration {iteration}")

            # Call Claude with tools
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=DOCGEN_AGENT_SYSTEM_PROMPT,
                tools=AGENT_TOOLS,
                messages=messages
            )

            # Check stop reason
            if response.stop_reason == "end_turn":
                # Agent finished - extract final response
                for block in response.content:
                    if hasattr(block, 'text'):
                        final_result = self._parse_agent_response(block.text)
                        break
                break

            elif response.stop_reason == "tool_use":
                # Agent wants to use tools
                tool_results = []

                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input

                        logger.info(f"Agent calling tool: {tool_name}")

                        # Execute tool
                        result = await tools.execute_tool(tool_name, tool_input)

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result)
                        })

                        # Check for duplicate - if found, we might stop early
                        if tool_name == "check_duplicate" and result.get("is_duplicate"):
                            logger.warning(f"Duplicate detected: {result.get('reason')}")

                # Add assistant response and tool results to messages
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

            else:
                logger.warning(f"Unexpected stop reason: {response.stop_reason}")
                break

        if not final_result:
            final_result = {
                "decision": "error",
                "explanation": "Agent did not produce a final result",
                "confidence": 0
            }

        logger.info(f"Agent decision: {final_result.get('decision')} (confidence: {final_result.get('confidence', 0)})")

        return final_result

    async def analyze_claim_data(
        self,
        claim_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze claim data (without documents) using AI reasoning.

        This is called when a claim is submitted without documents.
        The agent analyzes the claim metadata to detect fraud patterns.

        Args:
            claim_data: The claim submission data
            context: Contains existing_claims, policy_info

        Returns:
            Agent's decision and analysis results
        """
        logger.info(f"DocGen Agent analyzing claim data: {claim_data.get('claim_number')}")

        # Build prompt for claim analysis
        existing_claims = context.get("existing_claims", [])
        policy_info = context.get("policy_info", {})

        existing_claims_text = "None - this is the first claim for this policy."
        if existing_claims:
            claims_list = []
            for i, claim in enumerate(existing_claims, 1):
                claims_list.append(
                    f"  {i}. Claim #{claim.get('claim_number', 'N/A')} - "
                    f"{claim.get('claim_type', 'Unknown')} - "
                    f"{claim.get('service_date', 'N/A')} - "
                    f"${claim.get('claim_amount', 0):.2f} - "
                    f"Status: {claim.get('status', 'Unknown')}"
                )
            existing_claims_text = "\n".join(claims_list)

        claim_analysis_prompt = f"""You are a Pet Insurance Claims Analyst AI. Analyze this claim submission and make a decision.

## POLICY INFORMATION
- Policy ID: {policy_info.get('policy_id', claim_data.get('policy_id', 'Unknown'))}
- Customer ID: {claim_data.get('customer_id', 'Unknown')}
- Pet ID: {claim_data.get('pet_id', 'Unknown')}

## EXISTING CLAIMS FOR THIS POLICY
{existing_claims_text}

## NEW CLAIM TO ANALYZE
- Claim Number: {claim_data.get('claim_number', 'N/A')}
- Claim Type: {claim_data.get('claim_type', 'Unknown')}
- Category: {claim_data.get('claim_category', 'Unknown')}
- Service Date: {claim_data.get('service_date', 'N/A')}
- Claim Amount: ${claim_data.get('claim_amount', 0):.2f}
- Diagnosis Code: {claim_data.get('diagnosis_code', 'N/A')}
- Treatment Notes: {claim_data.get('treatment_notes', 'None provided')}
- Provider: {claim_data.get('provider_id', 'Unknown')}
- Is Emergency: {claim_data.get('is_emergency', False)}

## YOUR TASK
Analyze this claim and determine:
1. Is this claim legitimate or suspicious?
2. Are there any fraud patterns (duplicate claims, unusual amounts, suspicious timing)?
3. Should this claim be approved, reviewed, or denied?

## RESPOND WITH JSON:
{{
    "decision": "auto_approve" | "standard_review" | "manual_review" | "investigation" | "deny",
    "confidence": 0.0-1.0,
    "risk_score": 0-100,
    "explanation": "Your detailed reasoning",
    "fraud_indicators": ["list of any fraud indicators found"],
    "recommended_action": "specific recommendation",
    "extracted_data": {{
        "provider_name": "...",
        "service_date": "...",
        "total_amount": ...,
        "diagnosis": "..."
    }},
    "billing_info": {{
        "claim_amount": ...,
        "deductible_applied": 250,
        "amount_after_deductible": ...,
        "reimbursement_rate": 0.8,
        "final_payout": ...,
        "customer_responsibility": ...
    }}
}}
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": claim_analysis_prompt}]
            )

            # Parse response
            response_text = response.content[0].text if response.content else ""
            logger.info(f"AI claim analysis response: {response_text[:500]}...")

            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
                result["agent_decision"] = result.get("decision", "standard_review")
                result["thinking"] = result.get("explanation", "")
                return result
            else:
                logger.warning("Could not parse JSON from AI response")
                return {
                    "decision": "standard_review",
                    "agent_decision": "standard_review",
                    "confidence": 0.7,
                    "explanation": response_text,
                    "thinking": response_text
                }

        except Exception as e:
            logger.error(f"AI claim analysis error: {e}")
            return {
                "decision": "standard_review",
                "agent_decision": "standard_review",
                "confidence": 0.5,
                "explanation": f"AI analysis failed: {str(e)}",
                "thinking": f"Error during analysis: {str(e)}"
            }

    def _build_user_message(
        self,
        document_content: str,
        document_filename: str,
        document_hash: str,
        context: Dict[str, Any]
    ) -> str:
        """Build the user message with full context."""

        existing_claims = context.get("existing_claims", [])
        policy_info = context.get("policy_info", {})

        # Format existing claims for context
        existing_claims_text = "None - this is the first submission for this policy."
        if existing_claims:
            claims_list = []
            for i, claim in enumerate(existing_claims, 1):
                claims_list.append(
                    f"  {i}. Invoice #{claim.get('invoice_number', 'N/A')} - "
                    f"{claim.get('provider_name', 'Unknown')} - "
                    f"{claim.get('service_date', 'N/A')} - "
                    f"${claim.get('total_amount', 0):.2f}"
                )
            existing_claims_text = "\n".join(claims_list)

        return f"""## CONTEXT

### Policy Information
- Policy ID: {policy_info.get('policy_id', 'POL-DEFAULT')}
- Customer: {policy_info.get('customer_name', 'Unknown')}
- Pet: {policy_info.get('pet_name', 'Unknown')}
- Deductible: ${policy_info.get('deductible', 500):.2f}
- Reimbursement Rate: {policy_info.get('reimbursement_rate', 80)}%
- Annual Limit: ${policy_info.get('annual_limit', 10000):.2f}

### Existing Claims/Invoices for this Policy
{existing_claims_text}

---

## NEW DOCUMENT TO PROCESS

**Filename:** {document_filename}
**Content Hash:** {document_hash[:16]}...

### Document Content:
```
{document_content[:5000]}
```

---

## YOUR TASK

1. FIRST: Check if this document is a duplicate (compare against existing claims above)
2. If duplicate: STOP and explain why
3. If not duplicate: Extract data, validate, calculate billing, and submit

Respond with your analysis and decision in JSON format.
"""

    async def submit_claim(
        self,
        claim_data: Dict[str, Any],
        billing_info: Optional[Dict[str, Any]] = None,
        agent_decision: str = "standard_review",
        agent_reasoning: str = "",
        batch = None
    ) -> Dict[str, Any]:
        """
        Submit the claim to PetInsure360 backend.

        Args:
            claim_data: Extracted claim data from documents
            billing_info: Calculated billing information
            agent_decision: Agent's recommended decision
            agent_reasoning: Agent's explanation
            batch: The ProcessedBatch with customer/pet context
        """
        import httpx
        import os

        # PetInsure360 backend URL
        petinsure_url = os.getenv("PETINSURE_BACKEND_URL", "http://localhost:3002")

        # Get customer/pet data from batch if available
        customer_id = "UNKNOWN"
        pet_id = "UNKNOWN"
        pet_name = "Unknown"
        policy_id = None

        if batch:
            customer_id = batch.customer_id or (batch.claim_data.get("customer_id") if batch.claim_data else None) or "UNKNOWN"
            pet_id = batch.pet_id or (batch.claim_data.get("pet_id") if batch.claim_data else None) or "UNKNOWN"
            pet_name = batch.pet_name or (batch.claim_data.get("pet_name") if batch.claim_data else None) or "Unknown"
            policy_id = batch.policy_id or batch.policy_number or (batch.claim_data.get("policy_id") if batch.claim_data else None)

        # Prepare claim submission data
        # IMPORTANT: Set source="docgen_processed" to prevent circular batch creation
        submit_data = {
            "scenario_id": claim_data.get("scenario_id", "DOCGEN-UPLOAD"),
            "customer_id": customer_id,
            "pet_id": pet_id,
            "policy_id": policy_id,
            "claim_type": claim_data.get("claim_type", "Illness"),
            "claim_category": claim_data.get("diagnosis", "General")[:50] if claim_data.get("diagnosis") else "General",
            "diagnosis_code": claim_data.get("diagnosis_code", ""),
            "diagnosis": claim_data.get("diagnosis", ""),
            "service_date": claim_data.get("service_date", datetime.utcnow().date().isoformat()),
            "treatment_notes": claim_data.get("treatment_notes", agent_reasoning) or f"DocGen AI: {agent_reasoning}",
            "line_items": claim_data.get("line_items", []),
            "claim_amount": claim_data.get("total_amount", 0),
            "provider_id": claim_data.get("provider_id", ""),
            "provider_name": claim_data.get("provider_name", ""),
            "is_in_network": claim_data.get("is_in_network", True),
            "is_emergency": claim_data.get("is_emergency", False),
            "source": "docgen_processed"  # Flag to prevent circular batch creation
        }

        logger.info(f"Submitting claim to PetInsure360: customer={customer_id}, pet={pet_id}, amount={submit_data['claim_amount']}")

        # Try to submit to PetInsure360 backend
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{petinsure_url}/api/pipeline/submit-claim",
                    json=submit_data
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Claim created in PetInsure360: {result.get('claim_number')}")
                    return {
                        "claim_id": result.get("claim_id"),
                        "claim_number": result.get("claim_number"),
                        "status": "submitted",
                        "decision": agent_decision,
                        "reasoning": agent_reasoning,
                        "submitted_at": datetime.utcnow().isoformat(),
                        "claim_data": claim_data,
                        "billing_info": billing_info,
                        "petinsure_response": result
                    }
                else:
                    logger.warning(f"Failed to create claim in PetInsure360: {response.status_code} - {response.text}")
        except Exception as e:
            logger.warning(f"Could not connect to PetInsure360 backend: {e}")

        # Fallback: generate local claim ID if backend unavailable
        claim_id = f"CLM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{hash(str(claim_data)) % 10000:04X}"

        return {
            "claim_id": claim_id,
            "status": "submitted_local",
            "decision": agent_decision,
            "reasoning": agent_reasoning,
            "submitted_at": datetime.utcnow().isoformat(),
            "claim_data": claim_data,
            "billing_info": billing_info
        }

    def _parse_agent_response(self, text: str) -> Dict[str, Any]:
        """Parse the agent's final response."""
        try:
            # Try to find JSON in response
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0]
            elif "{" in text:
                # Find JSON object
                start = text.index("{")
                end = text.rindex("}") + 1
                json_str = text[start:end]
            else:
                return {
                    "decision": "error",
                    "explanation": "Could not parse agent response",
                    "raw_response": text
                }

            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Failed to parse agent response: {e}")
            return {
                "decision": "error",
                "explanation": str(e),
                "raw_response": text
            }
