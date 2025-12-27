"""
Material Event Taxonomy
=======================

SEC Form 8-K event categories and earnings event classifications for
Material Nonpublic Information (MNPI) analysis.

Per Section 6.2 of JLAW Zero-Dollar Transaction Forensic Specification v1.0.

Reference:
    - Section 6.2: Material Event Taxonomy
    - SEC Form 8-K Item Classification System
    - Regulation FD (Fair Disclosure) applicability
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class EventCategory:
    """
    Classification for material corporate events.
    
    Defines the MNPI sensitivity level and temporal proximity windows
    for each type of material event.
    
    Attributes:
        item: Event item number or identifier
        description: Human-readable event description
        mnpi_sensitivity: MNPI sensitivity level (CRITICAL, HIGH, MODERATE, LOW, VARIABLE)
        lookback_days: Days before event to flag suspicious transactions
        lookforward_days: Days after event to flag suspicious transactions
    """
    item: str
    description: str
    mnpi_sensitivity: str
    lookback_days: int
    lookforward_days: int


# SEC Form 8-K Event Taxonomy
# Per Section 6.2 of Zero-Dollar Transaction Forensic Specification
FORM_8K_EVENTS: Dict[str, EventCategory] = {
    "1.01": EventCategory(
        "1.01",
        "Entry into Material Definitive Agreement",
        "HIGH",
        30,
        5
    ),
    "1.02": EventCategory(
        "1.02",
        "Termination of Material Definitive Agreement",
        "HIGH",
        30,
        5
    ),
    "1.03": EventCategory(
        "1.03",
        "Bankruptcy or Receivership",
        "CRITICAL",
        60,
        2
    ),
    "2.01": EventCategory(
        "2.01",
        "Completion of Acquisition or Disposition of Assets",
        "HIGH",
        45,
        5
    ),
    "2.02": EventCategory(
        "2.02",
        "Results of Operations and Financial Condition",
        "CRITICAL",
        14,
        2
    ),
    "2.03": EventCategory(
        "2.03",
        "Creation of Direct Financial Obligation",
        "MODERATE",
        14,
        5
    ),
    "2.04": EventCategory(
        "2.04",
        "Triggering Events That Accelerate Obligations",
        "HIGH",
        14,
        2
    ),
    "2.05": EventCategory(
        "2.05",
        "Costs Associated with Exit or Disposal Activities",
        "HIGH",
        21,
        5
    ),
    "2.06": EventCategory(
        "2.06",
        "Material Impairments",
        "CRITICAL",
        21,
        2
    ),
    "3.01": EventCategory(
        "3.01",
        "Notice of Delisting or Transfer",
        "CRITICAL",
        30,
        2
    ),
    "4.01": EventCategory(
        "4.01",
        "Changes in Registrant's Certifying Accountant",
        "HIGH",
        14,
        5
    ),
    "4.02": EventCategory(
        "4.02",
        "Non-Reliance on Previously Issued Financial Statements",
        "CRITICAL",
        30,
        2
    ),
    "5.01": EventCategory(
        "5.01",
        "Changes in Control of Registrant",
        "CRITICAL",
        60,
        5
    ),
    "5.02": EventCategory(
        "5.02",
        "Departure/Appointment of Directors or Officers",
        "MODERATE",
        7,
        5
    ),
    "5.03": EventCategory(
        "5.03",
        "Amendments to Articles of Incorporation or Bylaws",
        "MODERATE",
        14,
        5
    ),
    "8.01": EventCategory(
        "8.01",
        "Other Events (Material)",
        "VARIABLE",
        30,
        5
    ),
}


# Earnings Events Taxonomy
# Per Section 6.2 of Zero-Dollar Transaction Forensic Specification
EARNINGS_EVENTS: Dict[str, EventCategory] = {
    "QUARTERLY_EARNINGS": EventCategory(
        "QUARTERLY",
        "Quarterly Earnings Release",
        "CRITICAL",
        14,
        2
    ),
    "ANNUAL_EARNINGS": EventCategory(
        "ANNUAL",
        "Annual Earnings Release",
        "CRITICAL",
        21,
        2
    ),
    "GUIDANCE_UPDATE": EventCategory(
        "GUIDANCE",
        "Earnings Guidance Update",
        "HIGH",
        7,
        2
    ),
    "PRE_ANNOUNCEMENT_POS": EventCategory(
        "PREANN_POS",
        "Pre-Announcement (Positive)",
        "HIGH",
        7,
        1
    ),
    "PRE_ANNOUNCEMENT_NEG": EventCategory(
        "PREANN_NEG",
        "Pre-Announcement (Negative)",
        "CRITICAL",
        14,
        1
    ),
}


def get_event_category(event_type: str) -> EventCategory:
    """
    Retrieve EventCategory by event type identifier.
    
    Args:
        event_type: Event type identifier (e.g., "1.01", "QUARTERLY_EARNINGS")
    
    Returns:
        EventCategory for the specified event type
    
    Raises:
        KeyError: If event_type is not found in taxonomy
    """
    # Check Form 8-K events first
    if event_type in FORM_8K_EVENTS:
        return FORM_8K_EVENTS[event_type]
    
    # Check earnings events
    if event_type in EARNINGS_EVENTS:
        return EARNINGS_EVENTS[event_type]
    
    raise KeyError(f"Unknown event type: {event_type}")


def get_all_event_types() -> Dict[str, EventCategory]:
    """
    Get combined dictionary of all event types.
    
    Returns:
        Dictionary mapping event type to EventCategory
    """
    all_events = {}
    all_events.update(FORM_8K_EVENTS)
    all_events.update(EARNINGS_EVENTS)
    return all_events


__all__ = [
    'EventCategory',
    'FORM_8K_EVENTS',
    'EARNINGS_EVENTS',
    'get_event_category',
    'get_all_event_types',
]
