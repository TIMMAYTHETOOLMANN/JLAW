# Detection Patterns API Reference

API reference for JLAW's 23 fraud detection algorithms.

## Pattern Detector

```python
from src.detection.advanced_pattern_detector import AdvancedPatternDetector

detector = AdvancedPatternDetector()
patterns = await detector.detect_all_patterns(filings)
```

## Pattern Categories

### Timing-Based (7 patterns)
- Options backdating (Erik Lie methodology)
- Spring loading
- Bullet dodging
- Pre-announcement trading
- Window dressing
- Quarter-end stuffing
- Cookie jar timing

### Statistical (8 patterns)
- Benford's Law deviations
- DSO analysis (channel stuffing)
- Revenue recognition anomalies
- Earnings smoothing
- Reserve manipulation
- Accrual anomalies
- Cash flow manipulation
- Asset impairment timing

### Comparative (8 patterns)
- Peer comparison outliers
- Industry benchmark deviations
- Historical trend breaks
- Seasonal adjustments
- Geographic anomalies
- Product mix shifts
- Margin compression
- Growth rate inconsistencies

**Accuracy Range**: 85-97% depending on pattern

---

See [Architecture Overview](../architecture/system_overview.md) for detection layer details.
