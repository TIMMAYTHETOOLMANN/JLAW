"""
Slack Alert Channel
==================

Sends alerts to Slack via webhook.

Usage:
    from src.alerting.channels.slack import SlackChannel
    from src.alerting.alert_manager import Alert, AlertSeverity
    
    channel = SlackChannel(webhook_url="https://hooks.slack.com/...")
    
    alert = Alert(
        title="Critical Violation",
        message="Insider trading detected",
        severity=AlertSeverity.CRITICAL,
        source="Node1"
    )
    
    await channel.send(alert)
"""

import aiohttp
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SlackChannel:
    """
    Slack webhook alert channel.
    
    Sends formatted alerts to Slack channels via incoming webhooks.
    """
    
    def __init__(self, webhook_url: str):
        """
        Initialize Slack channel.
        
        Args:
            webhook_url: Slack incoming webhook URL
        """
        self.webhook_url = webhook_url
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def send(self, alert) -> bool:
        """
        Send alert to Slack.
        
        Args:
            alert: Alert object to send
        
        Returns:
            True if sent successfully
        """
        if not self.webhook_url:
            self.logger.warning("Slack webhook URL not configured")
            return False
        
        # Format message for Slack
        payload = self._format_slack_message(alert)
        
        try:
            async with aiohttp.ClientSession(trust_env=True) as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        self.logger.info(f"Alert sent to Slack: {alert.title}")
                        return True
                    else:
                        text = await response.text()
                        self.logger.error(
                            f"Slack API error ({response.status}): {text}"
                        )
                        return False
        except Exception as e:
            self.logger.error(f"Error sending to Slack: {e}")
            return False
    
    def _format_slack_message(self, alert) -> Dict[str, Any]:
        """Format alert as Slack message."""
        # Severity emoji
        severity_emoji = {
            "debug": "🔍",
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }
        
        emoji = severity_emoji.get(alert.severity.value, "📢")
        
        # Color based on severity
        severity_colors = {
            "debug": "#808080",
            "info": "#36a64f",
            "warning": "#ff9900",
            "error": "#ff0000",
            "critical": "#ff0000"
        }
        
        color = severity_colors.get(alert.severity.value, "#808080")
        
        # Build Slack blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {alert.title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": alert.message
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Source:* {alert.source}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:* {alert.severity.value.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:* {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    }
                ]
            }
        ]
        
        # Add metadata if present
        if alert.metadata:
            metadata_text = "\n".join(
                f"• *{k}:* {v}" for k, v in alert.metadata.items()
            )
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Additional Info:*\n{metadata_text}"
                }
            })
        
        return {
            "blocks": blocks,
            "attachments": [
                {
                    "color": color,
                    "fallback": f"{alert.title}: {alert.message}"
                }
            ]
        }
