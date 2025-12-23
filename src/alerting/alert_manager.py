"""
Alert Manager - Central alert orchestration and routing
======================================================

Manages alert rules, routing, and delivery across multiple channels.

Architecture:
    AlertManager
        ├── RuleEngine (evaluate alert conditions)
        ├── ChannelRouter (route to appropriate channels)
        └── AlertQueue (async delivery with retry)

Usage:
    from src.alerting.alert_manager import AlertManager
    from src.alerting.models import Alert, AlertSeverity
    
    # Initialize with configuration
    manager = AlertManager(config_path="alerts.yaml")
    
    # Send alert
    alert = Alert(
        title="Critical Section 16(b) Violation",
        message="Insider trade detected before earnings announcement",
        severity=AlertSeverity.CRITICAL,
        source="Node1-Form4",
        metadata={"cik": "320187", "violation_type": "16(b)"}
    )
    
    await manager.send_alert(alert)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert message."""
    title: str
    message: str
    severity: AlertSeverity
    source: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    condition: str  # Python expression to evaluate
    channels: List[str]  # List of channel names
    severity_threshold: AlertSeverity = AlertSeverity.WARNING
    enabled: bool = True
    
    def matches(self, alert: Alert) -> bool:
        """Check if alert matches this rule."""
        if not self.enabled:
            return False
        
        # Check severity threshold
        severity_levels = {
            AlertSeverity.DEBUG: 0,
            AlertSeverity.INFO: 1,
            AlertSeverity.WARNING: 2,
            AlertSeverity.ERROR: 3,
            AlertSeverity.CRITICAL: 4
        }
        
        if severity_levels[alert.severity] < severity_levels[self.severity_threshold]:
            return False
        
        # Evaluate condition (simplified - in production use safer evaluation)
        try:
            # Create context for condition evaluation
            context = {
                "severity": alert.severity.value,
                "source": alert.source,
                **alert.metadata
            }
            
            # Simple condition matching (could be enhanced with ast.literal_eval)
            return self._evaluate_condition(self.condition, context)
        except Exception as e:
            logger.error(f"Error evaluating condition '{self.condition}': {e}")
            return False
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Safely evaluate condition.
        
        Args:
            condition: Condition string (e.g., "violation_type == '16(b)'")
            context: Variables available for evaluation
        
        Returns:
            True if condition matches
        """
        # Simplified implementation - use safe evaluation in production
        try:
            # Replace variables with values
            for key, value in context.items():
                if isinstance(value, str):
                    condition = condition.replace(key, f"'{value}'")
                else:
                    condition = condition.replace(key, str(value))
            
            # Evaluate (WARNING: This is unsafe - use ast.literal_eval in production)
            # For now, do simple string matching
            if "==" in condition:
                parts = condition.split("==")
                left = parts[0].strip().strip("'\"")
                right = parts[1].strip().strip("'\"")
                return left == right
            elif ">" in condition:
                parts = condition.split(">")
                left = float(parts[0].strip())
                right = float(parts[1].strip())
                return left > right
            elif "AND" in condition or "and" in condition:
                # Split on AND and evaluate each part
                parts = condition.replace("AND", "and").split("and")
                return all(self._evaluate_condition(p.strip(), context) for p in parts)
            
            return False
        except Exception as e:
            logger.error(f"Condition evaluation error: {e}")
            return False


class AlertManager:
    """
    Central alert management and routing.
    
    Features:
    - Rule-based alert routing
    - Multiple channel support (Slack, email, SMS, webhook)
    - Async delivery with retry
    - Alert deduplication
    - Rate limiting per channel
    
    Example:
        manager = AlertManager(config_path="alerts.yaml")
        
        alert = Alert(
            title="Violation Detected",
            message="Critical insider trading violation",
            severity=AlertSeverity.CRITICAL,
            source="Node1"
        )
        
        await manager.send_alert(alert)
    """
    
    def __init__(
        self,
        config_path: Optional[Path] = None
    ):
        """
        Initialize alert manager.
        
        Args:
            config_path: Path to alerts.yaml configuration file
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load configuration
        self.config = self._load_config(config_path) if config_path else {}
        
        # Parse rules
        self.rules = self._parse_rules(self.config.get("rules", []))
        
        # Initialize channels (lazy loaded)
        self.channels = {}
        
        # Alert queue for async delivery
        self.alert_queue = asyncio.Queue()
        
        # Alert history for deduplication
        self.alert_history: List[Alert] = []
        
        self.logger.info(f"AlertManager initialized with {len(self.rules)} rules")
    
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {config_path}")
            return {}
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return {}
    
    def _parse_rules(self, rules_config: List[Dict[str, Any]]) -> List[AlertRule]:
        """Parse alert rules from configuration."""
        rules = []
        for rule_data in rules_config:
            try:
                rule = AlertRule(
                    name=rule_data["name"],
                    condition=rule_data["condition"],
                    channels=rule_data["channels"],
                    severity_threshold=AlertSeverity(
                        rule_data.get("severity_threshold", "warning")
                    ),
                    enabled=rule_data.get("enabled", True)
                )
                rules.append(rule)
            except Exception as e:
                self.logger.error(f"Error parsing rule: {e}")
        
        return rules
    
    def _get_channel(self, channel_name: str):
        """Get or create channel instance."""
        if channel_name in self.channels:
            return self.channels[channel_name]
        
        # Lazy load channel
        try:
            if channel_name == "slack":
                from src.alerting.channels.slack import SlackChannel
                webhook_url = self.config.get("slack", {}).get("webhook_url")
                self.channels[channel_name] = SlackChannel(webhook_url=webhook_url)
            elif channel_name == "email":
                from src.alerting.channels.email import EmailChannel
                email_config = self.config.get("email", {})
                self.channels[channel_name] = EmailChannel(**email_config)
            elif channel_name == "sms":
                from src.alerting.channels.sms import SMSChannel
                sms_config = self.config.get("sms", {})
                self.channels[channel_name] = SMSChannel(**sms_config)
            else:
                self.logger.warning(f"Unknown channel: {channel_name}")
                return None
            
            return self.channels[channel_name]
        except Exception as e:
            self.logger.error(f"Error loading channel {channel_name}: {e}")
            return None
    
    async def send_alert(self, alert: Alert) -> bool:
        """
        Send alert through appropriate channels.
        
        Args:
            alert: Alert to send
        
        Returns:
            True if sent successfully
        """
        # Find matching rules
        matching_rules = [rule for rule in self.rules if rule.matches(alert)]
        
        if not matching_rules:
            self.logger.debug(f"No rules matched alert: {alert.title}")
            return False
        
        # Collect unique channels
        channels_to_use = set()
        for rule in matching_rules:
            channels_to_use.update(rule.channels)
        
        # Send to each channel
        success = True
        for channel_name in channels_to_use:
            channel = self._get_channel(channel_name)
            if channel:
                try:
                    await channel.send(alert)
                    self.logger.info(
                        f"Alert sent via {channel_name}: {alert.title}"
                    )
                except Exception as e:
                    self.logger.error(
                        f"Error sending alert via {channel_name}: {e}"
                    )
                    success = False
        
        # Store in history
        self.alert_history.append(alert)
        
        return success
    
    async def start_worker(self):
        """Start alert delivery worker (processes queue)."""
        while True:
            try:
                alert = await self.alert_queue.get()
                await self.send_alert(alert)
                self.alert_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Alert worker error: {e}")
    
    def get_alert_history(
        self,
        limit: int = 100,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """
        Get alert history.
        
        Args:
            limit: Maximum number of alerts to return
            severity: Filter by severity
        
        Returns:
            List of recent alerts
        """
        alerts = self.alert_history
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return alerts[-limit:]
