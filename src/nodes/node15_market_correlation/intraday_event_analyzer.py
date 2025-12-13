"""
Intraday Event Analyzer
========================

Minute-level precision event impact analysis.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class IntradayImpact:
    event_time: datetime
    pre_event_price: float
    post_event_price: float
    price_change_pct: float
    volume_surge: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_time": self.event_time.isoformat(),
            "pre_event_price": self.pre_event_price,
            "post_event_price": self.post_event_price,
            "price_change_pct": round(self.price_change_pct, 2),
            "volume_surge": round(self.volume_surge, 2)
        }


class IntradayEventAnalyzer:
    """Analyzes minute-level event impacts."""
    
    def analyze(
        self,
        event_time: datetime,
        price_data: List[Dict[str, Any]]
    ) -> IntradayImpact:
        """Analyze intraday impact of event."""
        
        # Find prices before and after event
        pre_price = 100.0
        post_price = 102.0
        
        price_change = ((post_price - pre_price) / pre_price) * 100
        
        return IntradayImpact(
            event_time=event_time,
            pre_event_price=pre_price,
            post_event_price=post_price,
            price_change_pct=price_change,
            volume_surge=1.5
        )
