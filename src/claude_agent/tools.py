"""
Forensic Tool Definitions for Claude Agent Tool Runner
=======================================================

Defines JSON Schema tool specifications for the Claude agentic loop.
Each tool maps to a specific JLAW pipeline module, enabling Claude to
invoke forensic analysis functions via structured tool_use blocks.

Tool descriptions follow Anthropic's guideline of 3-4+ sentences minimum,
explaining what the tool does, when to use it, and any caveats.
"""

from typing import Any

# ═══════════════════════════════════════════════════════════════════════
# Tool Definition Constants
# ═══════════════════════════════════════════════════════════════════════

FORENSIC_TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_sec_filings",
        "description": (
            "Search SEC EDGAR for filings by a specific company using CIK number. "
            "Returns matching filings filtered by form type and date range. "
            "Use this tool when you need to discover what SEC filings exist for a company "
            "before performing detailed analysis. Supports all SEC form types including "
            "Form 4, 10-K, 10-Q, 8-K, DEF 14A, 13F-HR, SC 13D/13G, and Form 144."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cik": {
                    "type": "string",
                    "description": "SEC Central Index Key (CIK) number for the company.",
                },
                "form_type": {
                    "type": "string",
                    "description": "SEC form type to filter by (e.g., '4', '10-K', '10-Q', '8-K').",
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date for filing search in YYYY-MM-DD format.",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date for filing search in YYYY-MM-DD format.",
                },
            },
            "required": ["cik"],
        },
    },
    {
        "name": "analyze_filing",
        "description": (
            "Perform deep forensic analysis on a specific SEC filing document. "
            "Extracts violations, red flags, and anomalies from the filing content. "
            "Use this tool after discovering filings via search_sec_filings to analyze "
            "individual documents for securities law violations, SOX compliance issues, "
            "insider trading patterns, and financial statement fraud indicators."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "document_url": {
                    "type": "string",
                    "description": "Full URL to the SEC EDGAR filing document.",
                },
                "filing_type": {
                    "type": "string",
                    "description": "SEC form type (e.g., '4', '10-K', 'DEF 14A').",
                },
                "cik": {
                    "type": "string",
                    "description": "Company CIK number for context.",
                },
                "filing_date": {
                    "type": "string",
                    "description": "Filing date in YYYY-MM-DD format.",
                },
            },
            "required": ["document_url", "filing_type", "cik"],
        },
    },
    {
        "name": "detect_insider_trading",
        "description": (
            "Analyze Form 4 insider trading filings for Section 16(a) late filing "
            "violations, short-swing profit violations under Section 16(b), and "
            "suspicious trading patterns. Use this tool specifically for Form 3, 4, "
            "and 5 filings to detect insider trading anomalies such as trades preceding "
            "material announcements, zero-dollar transactions, and clustered selling."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cik": {
                    "type": "string",
                    "description": "Company CIK number.",
                },
                "insider_cik": {
                    "type": "string",
                    "description": "CIK of the insider/officer being investigated.",
                },
                "start_date": {
                    "type": "string",
                    "description": "Analysis window start date in YYYY-MM-DD format.",
                },
                "end_date": {
                    "type": "string",
                    "description": "Analysis window end date in YYYY-MM-DD format.",
                },
            },
            "required": ["cik"],
        },
    },
    {
        "name": "calculate_penalty",
        "description": (
            "Calculate statutory penalty exposure under SEC, DOJ, or IRS enforcement "
            "frameworks based on identified violations. Computes potential fines, "
            "disgorgement amounts, and criminal referral thresholds. Use this tool after "
            "identifying specific violations to quantify the legal and financial exposure. "
            "Supports penalty calculation under 15 USC § 78u, SOX § 906, and IRC § 83."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "statute": {
                    "type": "string",
                    "description": "Statutory provision (e.g., '15 USC § 78u', 'SOX § 906').",
                },
                "violation_type": {
                    "type": "string",
                    "description": "Type of violation detected.",
                },
                "violation_count": {
                    "type": "integer",
                    "description": "Number of separate violations detected.",
                },
                "estimated_damages": {
                    "type": "number",
                    "description": "Estimated financial damages from the violations.",
                },
                "aggravating_factors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of aggravating factors (e.g., 'repeat_offender').",
                },
            },
            "required": ["statute", "violation_type", "violation_count"],
        },
    },
    {
        "name": "check_whistleblower_eligibility",
        "description": (
            "Evaluate whether identified violations qualify for whistleblower bounty "
            "programs at the SEC, CFTC, IRS, or DOJ. Calculates estimated bounty "
            "range based on sanctions potential and program-specific rules. Use this "
            "tool after violations have been detected and penalties calculated to assess "
            "whistleblower reward potential under Dodd-Frank Section 21F (SEC program "
            "pays 10-30% of sanctions exceeding $1M)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "agency": {
                    "type": "string",
                    "enum": ["SEC", "CFTC", "IRS", "DOJ"],
                    "description": "Enforcement agency for the whistleblower program.",
                },
                "violation_type": {
                    "type": "string",
                    "description": "Type of violation being reported.",
                },
                "estimated_sanctions": {
                    "type": "number",
                    "description": "Estimated total sanctions amount.",
                },
                "evidence_quality": {
                    "type": "string",
                    "enum": ["strong", "moderate", "weak"],
                    "description": "Overall quality of supporting evidence.",
                },
            },
            "required": ["agency", "violation_type", "estimated_sanctions"],
        },
    },
    {
        "name": "query_evidence_chain",
        "description": (
            "Query the FRE 902(13)/(14) compliant evidence chain for a specific "
            "investigation. Returns custody records, hash integrity verification "
            "results (SHA-256 + SHA3-512 + BLAKE2b), and Merkle tree proof paths. "
            "Use this tool to verify evidence integrity or retrieve the chain of "
            "custody for specific documents in the investigation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "investigation_id": {
                    "type": "string",
                    "description": "Unique identifier for the investigation.",
                },
                "document_hash": {
                    "type": "string",
                    "description": "SHA-256 hash of the document to verify.",
                },
                "query_type": {
                    "type": "string",
                    "enum": ["custody_chain", "hash_verify", "merkle_proof"],
                    "description": "Type of evidence chain query to perform.",
                },
            },
            "required": ["investigation_id", "query_type"],
        },
    },
    {
        "name": "run_detection_pattern",
        "description": (
            "Execute a specific fraud detection algorithm from the JLAW 23-pattern "
            "detection suite. Includes options backdating (Erik Lie methodology), "
            "channel stuffing (DSO analysis), spring loading, bullet dodging, "
            "round-tripping, and cookie jar reserves detection. Use this tool to "
            "apply targeted quantitative analysis after initial filing review "
            "identifies potential fraud indicators."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern_name": {
                    "type": "string",
                    "enum": [
                        "options_backdating",
                        "channel_stuffing",
                        "spring_loading",
                        "bullet_dodging",
                        "round_tripping",
                        "cookie_jar_reserves",
                        "revenue_recognition_fraud",
                        "related_party_concealment",
                    ],
                    "description": "Detection pattern algorithm to execute.",
                },
                "cik": {
                    "type": "string",
                    "description": "Company CIK number.",
                },
                "start_date": {
                    "type": "string",
                    "description": "Analysis period start date in YYYY-MM-DD format.",
                },
                "end_date": {
                    "type": "string",
                    "description": "Analysis period end date in YYYY-MM-DD format.",
                },
            },
            "required": ["pattern_name", "cik"],
        },
    },
    {
        "name": "generate_investigation_state",
        "description": (
            "Create or update the investigation state document that tracks the "
            "current phase, key findings, outstanding gaps, and in-progress "
            "analysis. This structured state reduces context from tens of thousands "
            "of tokens to 500-2000 tokens for efficient continuation of long-running "
            "investigations. Call this tool periodically during multi-step analyses."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "investigation_id": {
                    "type": "string",
                    "description": "Unique identifier for the investigation.",
                },
                "phase": {
                    "type": "string",
                    "description": "Current investigation phase.",
                },
                "findings": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key findings discovered so far.",
                },
                "gaps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Outstanding investigation gaps to address.",
                },
            },
            "required": ["investigation_id", "phase"],
        },
    },
]


def get_forensic_tools() -> list[dict[str, Any]]:
    """Return the full set of forensic tool definitions.

    Returns:
        List of tool definition dicts in Anthropic tool_use JSON Schema format.
    """
    return FORENSIC_TOOLS


def get_tools_by_names(names: list[str]) -> list[dict[str, Any]]:
    """Return a subset of forensic tools by name.

    Args:
        names: List of tool names to include.

    Returns:
        Filtered list of tool definitions.
    """
    return [t for t in FORENSIC_TOOLS if t["name"] in names]


def get_tool_names() -> list[str]:
    """Return all available tool names.

    Returns:
        List of tool name strings.
    """
    return [t["name"] for t in FORENSIC_TOOLS]
