"""Security utilities and validation."""

import time
from typing import Dict, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta
import structlog
from telegram import Message
from telegram.ext import BaseRateLimiter

from .config import settings

logger = structlog.get_logger(__name__)


class RateLimiter(BaseRateLimiter):
    """Custom rate limiter for Telegram bot."""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.max_requests = settings.rate_limit_requests
        self.window = settings.rate_limit_window
    
    async def initialize(self):
        """Initialize the rate limiter."""
        pass
    
    async def shutdown(self):
        """Shutdown the rate limiter."""
        pass
    
    async def process_request(
        self,
        callback,
        args,
        kwargs,
        endpoint: str,
        data: Dict[str, Any],
    ):
        """Process request with rate limiting."""
        user_id = data.get('chat_id', 'unknown')
        current_time = time.time()
        
        # Clean old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if current_time - req_time < self.window
        ]
        
        # Check rate limit
        if len(self.requests[user_id]) >= self.max_requests:
            logger.warning("Rate limit exceeded", user_id=user_id, endpoint=endpoint)
            raise Exception("Rate limit exceeded")
        
        # Add current request
        self.requests[user_id].append(current_time)
        
        # Execute callback
        return await callback(*args, **kwargs)


class InputValidator:
    """Input validation and sanitization."""
    
    def __init__(self):
        self.max_message_length = 10000
        self.max_username_length = 100
        self.blocked_patterns = [
            # SQL injection attempts
            r"(?i)(union|select|insert|update|delete|drop|create|alter)\s+",
            # Script injection
            r"<script[^>]*>.*?</script>",
            # Command injection
            r"[;&|`$(){}[\]\\]",
        ]
    
    def validate_message(self, message: Message) -> bool:
        """Validate incoming message."""
        try:
            # Check message text length
            text = message.text or message.caption or ''
            if len(text) > self.max_message_length:
                logger.warning("Message too long", length=len(text))
                return False
            
            # Check username length
            if message.from_user and message.from_user.username:
                if len(message.from_user.username) > self.max_username_length:
                    logger.warning("Username too long", username=message.from_user.username)
                    return False
            
            # Check for suspicious patterns
            if self._contains_suspicious_patterns(text):
                logger.warning("Suspicious patterns detected in message")
                return False
            
            return True
            
        except Exception as e:
            logger.error("Message validation failed", error=str(e))
            return False
    
    def _contains_suspicious_patterns(self, text: str) -> bool:
        """Check for suspicious patterns in text."""
        import re
        
        for pattern in self.blocked_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def sanitize_text(self, text: str) -> str:
        """Sanitize text input."""
        if not text:
            return ''
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Limit length
        if len(text) > self.max_message_length:
            text = text[:self.max_message_length]
        
        return text.strip()


# CryptoUtils class removed - was not being used in the application


class SecurityMonitor:
    """Monitor security events and anomalies."""
    
    def __init__(self):
        self.failed_attempts = defaultdict(list)
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
    
    def record_failed_attempt(self, identifier: str):
        """Record a failed attempt."""
        current_time = datetime.now()
        self.failed_attempts[identifier].append(current_time)
        
        # Clean old attempts
        cutoff_time = current_time - self.lockout_duration
        self.failed_attempts[identifier] = [
            attempt for attempt in self.failed_attempts[identifier]
            if attempt > cutoff_time
        ]
        
        logger.warning(
            "Failed attempt recorded",
            identifier=identifier,
            attempts=len(self.failed_attempts[identifier])
        )
    
    def is_locked_out(self, identifier: str) -> bool:
        """Check if identifier is locked out."""
        current_time = datetime.now()
        cutoff_time = current_time - self.lockout_duration
        
        recent_attempts = [
            attempt for attempt in self.failed_attempts.get(identifier, [])
            if attempt > cutoff_time
        ]
        
        return len(recent_attempts) >= self.max_failed_attempts
    
    def clear_attempts(self, identifier: str):
        """Clear failed attempts for identifier."""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]


# Global security instances
rate_limiter = RateLimiter()
input_validator = InputValidator()
security_monitor = SecurityMonitor()

