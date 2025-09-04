# 🔒 Security Module

Security utilities including rate limiting, input validation, and security monitoring.

## Overview

The security module provides three main components:

- **RateLimiter** - Prevents API abuse and spam
- **InputValidator** - Sanitizes and validates user input
- **SecurityMonitor** - Tracks security events and failed attempts

## Components

### 1. RateLimiter

Custom rate limiter for Telegram bot API calls.

#### Configuration
```bash
# Rate limiting settings
RATE_LIMIT_REQUESTS=100    # Max requests per window
RATE_LIMIT_WINDOW=3600     # Window in seconds (1 hour)
```

#### How It Works
```python
# Rate limiter tracks requests per user
user_requests = {
    "user_123": [timestamp1, timestamp2, ...],
    "user_456": [timestamp1, timestamp2, ...]
}

# Check if user exceeds limit
if len(user_requests[user_id]) > max_requests:
    raise RateLimitExceeded
```

#### Usage
```python
from src.security import rate_limiter

# Rate limiter is automatically used by Telegram bot
# No manual configuration needed
```

**Note**: The rate limiter is currently not being called by the Telegram bot library. This may be due to interface changes in python-telegram-bot v20.7.

### 2. InputValidator

Validates and sanitizes input data to prevent injection attacks.

#### Validation Rules

| Input Type | Validation | Example |
|------------|------------|---------|
| **Message Text** | Length, characters | Max 4096 chars, no null bytes |
| **User ID** | Numeric, range | Positive integer |
| **Group ID** | Numeric, negative | Negative integer |
| **File ID** | Format, length | Telegram file ID format |

#### Usage Examples
```python
from src.security import input_validator

# Validate message text
is_valid = input_validator.validate_message_text("Hello world")
if not is_valid:
    logger.warning("Invalid message text detected")

# Validate user ID
is_valid = input_validator.validate_user_id(12345)
if not is_valid:
    logger.warning("Invalid user ID")

# Validate group ID
is_valid = input_validator.validate_group_id(-1001234567890)
if not is_valid:
    logger.warning("Invalid group ID")
```

#### Validation Methods
```python
class InputValidator:
    def validate_message_text(self, text: str) -> bool:
        """Validate message text content."""
        
    def validate_user_id(self, user_id: int) -> bool:
        """Validate Telegram user ID."""
        
    def validate_group_id(self, group_id: int) -> bool:
        """Validate Telegram group ID."""
        
    def validate_file_id(self, file_id: str) -> bool:
        """Validate Telegram file ID."""
```

### 3. SecurityMonitor

Tracks security events and failed attempts for monitoring.

#### Features
- **Failed Attempt Tracking** - Monitors repeated failures
- **Automatic Cleanup** - Removes old failed attempts
- **Security Event Logging** - Records suspicious activity
- **Threshold Monitoring** - Alerts on excessive failures

#### Usage
```python
from src.security import security_monitor

# Track failed attempt
security_monitor.record_failed_attempt("user_123", "invalid_token")

# Check if user is blocked
is_blocked = security_monitor.is_blocked("user_123")

# Get security statistics
stats = security_monitor.get_security_stats()
```

#### Security Statistics
```python
{
    "total_failed_attempts": 45,
    "blocked_users": 3,
    "recent_attempts": [
        {
            "identifier": "user_123",
            "attempts": 5,
            "last_attempt": "2025-01-04T12:00:00Z",
            "blocked": True
        }
    ]
}
```

## Security Features

### Input Sanitization
```python
# Remove dangerous characters
def sanitize_input(text: str) -> str:
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32)
    
    # Limit length
    return text[:4096]
```

### Rate Limiting Algorithm
```python
async def process_request(self, callback, args, kwargs, endpoint, data):
    user_id = data.get('chat_id', 'unknown')
    current_time = time.time()
    
    # Clean old requests
    self.requests[user_id] = [
        req_time for req_time in self.requests[user_id]
        if current_time - req_time < self.window
    ]
    
    # Check rate limit
    if len(self.requests[user_id]) >= self.max_requests:
        raise RateLimitExceeded("Rate limit exceeded")
    
    # Record request
    self.requests[user_id].append(current_time)
    
    # Execute callback
    return await callback(*args, **kwargs)
```

### Failed Attempt Tracking
```python
def record_failed_attempt(self, identifier: str, reason: str):
    """Record a failed security attempt."""
    current_time = datetime.now()
    
    if identifier not in self.failed_attempts:
        self.failed_attempts[identifier] = []
    
    self.failed_attempts[identifier].append({
        'timestamp': current_time,
        'reason': reason
    })
    
    # Cleanup old attempts
    self._cleanup_failed_attempts(identifier)
```

## Configuration

### Environment Variables
```bash
# Rate limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Security monitoring
MAX_FAILED_ATTEMPTS=5
FAILED_ATTEMPT_WINDOW=3600
```

### Security Thresholds
| Setting | Default | Description |
|---------|---------|-------------|
| **Max Requests** | 100 | Requests per window |
| **Window Size** | 3600s | Rate limit window |
| **Max Failed Attempts** | 5 | Before blocking |
| **Block Duration** | 3600s | How long to block |

## Integration

### Telegram Bot Integration
```python
# Rate limiter is passed to bot application
application = Application.builder() \
    .token(settings.telegram_bot_token) \
    .rate_limiter(rate_limiter) \
    .build()
```

### Input Validation Integration
```python
# Validate inputs before processing
async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    
    # Validate message text
    if not input_validator.validate_message_text(message.text):
        logger.warning("Invalid message text", user_id=message.from_user.id)
        return
    
    # Validate user ID
    if not input_validator.validate_user_id(message.from_user.id):
        logger.warning("Invalid user ID", user_id=message.from_user.id)
        return
    
    # Process message...
```

## Monitoring & Alerts

### Security Events
```python
# Log security events
logger.warning("Rate limit exceeded", 
              user_id=user_id, 
              endpoint=endpoint,
              request_count=len(self.requests[user_id]))

logger.warning("Invalid input detected",
              input_type="message_text",
              user_id=user_id,
              input_length=len(text))
```

### Security Statistics
```python
# Get security metrics
stats = security_monitor.get_security_stats()

# Monitor failed attempts
if stats['total_failed_attempts'] > 100:
    logger.critical("High number of failed attempts detected")
```

## Troubleshooting

### Rate Limiter Not Working
- ✅ **Check Telegram bot version** - Interface may have changed
- ✅ **Verify rate limiter integration** - Ensure it's passed to Application
- ✅ **Check configuration** - Verify rate limit settings
- ✅ **Monitor logs** - Look for rate limit messages

### Input Validation Issues
- ✅ **Check validation rules** - Review validation logic
- ✅ **Test with sample data** - Verify validation works
- ✅ **Review error logs** - Check for validation failures
- ✅ **Update validation patterns** - Adjust for new requirements

### Security Monitoring Problems
- ✅ **Check failed attempt tracking** - Verify recording works
- ✅ **Review cleanup logic** - Ensure old attempts are removed
- ✅ **Monitor memory usage** - Check for memory leaks
- ✅ **Test blocking logic** - Verify users are blocked correctly

---

**💡 Pro Tip**: Monitor the security statistics regularly to identify potential attacks or abuse patterns. Use the `/stats` endpoint to view current security metrics.
