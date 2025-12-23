"""
JLAW Alerting System
===================

Multi-channel alert management and routing for forensic analysis events.

Features:
- Rule-based alert routing
- Multiple channels (Slack, Email, SMS)
- Async delivery with retry
- Alert deduplication
- Rate limiting

Usage:
    from src.alerting import AlertManager, Alert, AlertSeverity
    
    # Initialize with configuration
    manager = AlertManager(config_path="alerts.yaml")
    
    # Create and send alert
    alert = Alert(
        title="Critical Violation Detected",
        message="Insider trading violation in Form 4 filing",
        severity=AlertSeverity.CRITICAL,
        source="Node1-Form4",
        metadata={"cik": "320187", "violation_type": "16(b)"}
    )
    
    await manager.send_alert(alert)
"""

from .alert_manager import AlertManager, Alert, AlertSeverity, AlertRule

__all__ = ["AlertManager", "Alert", "AlertSeverity", "AlertRule"]
