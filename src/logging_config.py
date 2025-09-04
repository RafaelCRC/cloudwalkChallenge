"""Structured logging configuration."""

import os
import sys
import logging
from typing import Dict, Any
import structlog
from datetime import datetime

from .config import settings


def configure_logging():
    """Configure structured logging with security and monitoring."""
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Configure standard logging
    numeric_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )
    logging.getLogger().setLevel(numeric_level)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Add file handler for persistent logging
    log_file = os.path.join(log_dir, f"fraud_monitor_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    
    # Security: Filter sensitive data from logs
    add_security_filter()


def add_security_filter():
    """Add security filter to prevent logging sensitive data."""
    
    class SecurityFilter(logging.Filter):
        """Filter to redact sensitive information from logs."""
        
        SENSITIVE_PATTERNS = [
            'password',
            'token',
            'key',
            'secret',
            'credit',
            'card',
            'cvv',
            'ssn',
            'account'
        ]
        
        TELEGRAM_TOKEN_PATTERN = re.compile(r"bot[0-9A-Za-z:]+")
        
        def filter(self, record):
            """Filter log record to remove sensitive data."""
            if hasattr(record, 'msg') and isinstance(record.msg, str):
                msg_lower = record.msg.lower()
                # Redact sensitive keywords
                for pattern in self.SENSITIVE_PATTERNS:
                    if pattern in msg_lower:
                        record.msg = "[REDACTED - SENSITIVE DATA]"
                        return True
                # Redact Telegram token patterns
                record.msg = self.TELEGRAM_TOKEN_PATTERN.sub("[REDACTED_TOKEN]", record.msg)
            return True
    
    # Apply filter to all handlers
    security_filter = SecurityFilter()
    root_logger = logging.getLogger()
    
    for handler in root_logger.handlers:
        handler.addFilter(security_filter)


class AuditLogger:
    """Audit logger for security events."""
    
    def __init__(self):
        self.logger = structlog.get_logger("audit")
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related events."""
        self.logger.info(
            "Security event",
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            **details
        )
    
    def log_fraud_alert(self, alert_data: Dict[str, Any]):
        """Log fraud detection alerts."""
        self.logger.warning(
            "Fraud alert generated",
            alert_type=alert_data.get('type'),
            confidence=alert_data.get('score'),
            keywords=alert_data.get('keywords', []),
            timestamp=datetime.now().isoformat()
        )
    
    def log_access_attempt(self, user_id: str, success: bool, details: Dict[str, Any] = None):
        """Log access attempts."""
        self.logger.info(
            "Access attempt",
            user_id=user_id,
            success=success,
            timestamp=datetime.now().isoformat(),
            **(details or {})
        )


# Global audit logger instance
audit_logger = AuditLogger()

