"""Node 8: 13D/13G Beneficial Ownership Tracker.

Provides comprehensive analysis of Schedule 13D/13G filings for:
- Beneficial ownership threshold monitoring (5%+)
- Activist investor intent signal detection
- 13D → 13G conversion tracking
- December 2024 rule compliance verification
"""

from .beneficial_ownership_tracker import BeneficialOwnershipTracker
from .beneficial_ownership_tracker_v2 import BeneficialOwnershipTrackerV2

__all__ = [
    'BeneficialOwnershipTracker',
    'BeneficialOwnershipTrackerV2',
]
