"""
SMS Alert Channel
================

Sends alerts via SMS using Twilio.

Usage:
    from src.alerting.channels.sms import SMSChannel
    from src.alerting.alert_manager import Alert, AlertSeverity
    
    channel = SMSChannel(
        account_sid="AC...",
        auth_token="...",
        from_phone="+15555551234",
        to_phones=["+15555555678"]
    )
    
    alert = Alert(
        title="Critical Violation",
        message="Insider trading detected",
        severity=AlertSeverity.CRITICAL,
        source="Node1"
    )
    
    await channel.send(alert)
"""

import asyncio
import logging
from typing import List

logger = logging.getLogger(__name__)


class SMSChannel:
    """
    SMS alert channel using Twilio.
    
    Sends short alert messages via SMS to configured phone numbers.
    """
    
    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_phone: str,
        to_phones: List[str]
    ):
        """
        Initialize SMS channel.
        
        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_phone: Sender phone number (E.164 format)
            to_phones: List of recipient phone numbers (E.164 format)
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_phone = from_phone
        self.to_phones = to_phones
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Lazy load Twilio client
        self._client = None
    
    @property
    def client(self):
        """Lazy load Twilio client."""
        if self._client is None:
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
            except ImportError:
                self.logger.error(
                    "Twilio library not installed. Install with: pip install twilio"
                )
                raise
        return self._client
    
    async def send(self, alert) -> bool:
        """
        Send alert via SMS.
        
        Args:
            alert: Alert object to send
        
        Returns:
            True if sent successfully
        """
        # Build SMS message (max 160 chars for single SMS)
        message = self._format_sms_message(alert)
        
        # Send to all recipients
        success = True
        for phone in self.to_phones:
            try:
                await asyncio.to_thread(
                    self._send_sms,
                    phone,
                    message
                )
                self.logger.info(f"Alert sent via SMS to {phone}: {alert.title}")
            except Exception as e:
                self.logger.error(f"Error sending SMS to {phone}: {e}")
                success = False
        
        return success
    
    def _format_sms_message(self, alert) -> str:
        """
        Format alert as SMS message (max 160 chars).
        
        Args:
            alert: Alert object
        
        Returns:
            Formatted SMS message
        """
        # Severity prefix
        severity_prefix = {
            "debug": "DEBUG",
            "info": "INFO",
            "warning": "WARN",
            "error": "ERROR",
            "critical": "CRIT"
        }
        
        prefix = severity_prefix.get(alert.severity.value, "ALERT")
        
        # Build short message
        # Format: [CRIT] Title | Message (truncated to 160 chars)
        message = f"[{prefix}] {alert.title} | {alert.message}"
        
        # Truncate to 160 chars if needed
        if len(message) > 160:
            message = message[:157] + "..."
        
        return message
    
    def _send_sms(self, to_phone: str, message: str):
        """
        Send SMS via Twilio (synchronous).
        
        Args:
            to_phone: Recipient phone number
            message: SMS message text
        """
        self.client.messages.create(
            body=message,
            from_=self.from_phone,
            to=to_phone
        )
