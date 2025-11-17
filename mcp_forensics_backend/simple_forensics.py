"""
Simplified forensics system for testing without heavy ML dependencies
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger("SIMPLE_FORENSICS")


class SimpleForensicInvestigator:
    """Simplified forensic investigator for testing"""

    def __init__(self, db_path: str = "forensic_evidence.db"):
        self.db_path = db_path
        logger.info("Simple forensic investigator initialized")

    async def investigate_company(
        self, cik: str, years_back: int = 3, forms: List[str] = None
    ) -> Dict[str, Any]:
        """Simplified investigation that returns mock results"""

        if forms is None:
            forms = ["10-K", "10-Q", "8-K"]

        logger.info(f"Starting investigation for CIK {cik}, {years_back} years, forms: {forms}")

        # Simulate processing time
        await asyncio.sleep(2)

        # Generate mock investigation results
        investigation_id = f"INV_{cik}_{int(datetime.utcnow().timestamp())}"

        results = {
            "investigation_id": investigation_id,
            "cik": cik,
            "years_back": years_back,
            "forms": forms,
            "filings_analyzed": years_back * len(forms) * 4,  # Mock: 4 filings per form per year
            "risk_score": 0.35,  # Mock risk score
            "risk_level": "MEDIUM",
            "fraud_indicators": [
                {
                    "type": "LATE_FILING",
                    "severity": 0.6,
                    "description": "Multiple late filings detected",
                    "count": 3,
                },
                {
                    "type": "REVENUE_ANOMALY",
                    "severity": 0.4,
                    "description": "Unusual revenue patterns",
                    "count": 2,
                },
            ],
            "criminal_exposure": ["15 USC 78j(b)", "15 USC 78m"],
            "civil_exposure": ["Rule 10b-5", "Section 13"],
            "executive_summary": f"Investigation {investigation_id} completed. "
            + f"Analyzed {years_back * len(forms) * 4} filings. "
            + "Risk level: MEDIUM (35% confidence). "
            + "2 potential fraud indicators identified.",
            "duration": 2.0,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed",
        }

        logger.info(f"Investigation {investigation_id} completed")
        return results

    class db:
        """Mock database interface"""

        @staticmethod
        def get_high_risk_companies(threshold: float):
            """Return mock high-risk companies"""
            return [
                {"cik": "0001318605", "ticker": "TSLA", "risk_score": 0.73, "name": "Tesla Inc."},
                {"cik": "0001065280", "ticker": "NFLX", "risk_score": 0.68, "name": "Netflix Inc."},
            ]

        @staticmethod
        def get_stats():
            """Return mock database statistics"""
            return {
                "total_investigations": 10,
                "total_companies": 8,
                "average_risk_score": 0.42,
                "high_risk_count": 2,
                "database_size_mb": 15.3,
            }
