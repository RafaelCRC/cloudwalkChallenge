# 📝 Logging Configuration

Structured logging system with security filtering and audit capabilities.

## Overview

The logging system provides:
- **Structured JSON logs** for easy parsing
- **Security filtering** to prevent sensitive data exposure
- **File and console output** for different use cases
- **Audit logging** for security events
- **Configurable levels** via environment variables

## Quick Setup

```python
from src.logging_config import configure_logging, audit_logger

# Initialize logging (called automatically in main.py)
configure_logging()

# Log security events
audit_logger.log_security_event("login_attempt", {"user_id": "123"})
```

## Log Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| `DEBUG` | Detailed diagnostic info | Development, troubleshooting |
| `INFO` | General information | Normal operation |
| `WARNING` | Something unexpected | Potential issues |
| `ERROR` | Error occurred | Problems need attention |
| `CRITICAL` | Serious error | System failure |

### Setting Log Level
```bash
# In .env file
LOG_LEVEL=DEBUG

# Or via environment
export LOG_LEVEL=INFO
```

## Log Output Formats

### Console Output (JSON)
```json
{
  "event": "Message processed",
  "message_id": 12345,
  "chat_id": -1001234567890,
  "message_type": "text",
  "logger": "src.telegram_bot",
  "level": "info",
  "timestamp": "2025-01-04T12:00:00.000000Z"
}
```

### File Output
- **Location**: `logs/fraud_monitor_YYYYMMDD.log`
- **Format**: Same JSON structure
- **Rotation**: Daily files
- **Retention**: Manual cleanup required

## Security Features

### Sensitive Data Filtering
Automatically redacts sensitive patterns:

| Pattern | Example | Result |
|---------|---------|--------|
| `password` | "password123" | `[REDACTED - SENSITIVE DATA]` |
| `token` | "bot123:ABC" | `[REDACTED - SENSITIVE DATA]` |
| `key` | "secret_key" | `[REDACTED - SENSITIVE DATA]` |
| `credit` | "credit card" | `[REDACTED - SENSITIVE DATA]` |
| `card` | "card number" | `[REDACTED - SENSITIVE DATA]` |

### Audit Logging
Special logger for security events:

```python
# Security events
audit_logger.log_security_event("access_attempt", {
    "user_id": "12345",
    "ip_address": "192.168.1.1",
    "success": True
})

# Fraud alerts
audit_logger.log_fraud_alert({
    "type": "high_risk_fraud",
    "score": 0.8,
    "keywords": ["paypal", "verify"]
})
```

## Configuration Details

### Structlog Setup
```python
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,      # Filter by log level
        structlog.stdlib.add_logger_name,      # Add logger name
        structlog.stdlib.add_log_level,        # Add log level
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="ISO"),  # ISO timestamps
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,  # Exception formatting
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()    # JSON output
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

### Standard Logging
```python
logging.basicConfig(
    format="%(message)s",           # Simple format (JSON handles structure)
    stream=sys.stdout,              # Console output
    level=getattr(logging, settings.log_level.upper()),
)
```

## Usage in Code

### Basic Logging
```python
import structlog

logger = structlog.get_logger(__name__)

# Info level
logger.info("Message processed", 
           message_id=12345, 
           chat_id=-1001234567890)

# Debug level
logger.debug("Processing image", 
            file_id="BAADBAADrQADBREAAYag2ej2gfshAg")

# Error level
logger.error("Database connection failed", 
            error=str(e), 
            retry_count=3)
```

### Structured Data
```python
# Good: Structured data
logger.info("Fraud alert created",
           alert_id=42,
           alert_type="high_risk_fraud",
           confidence_score=0.8,
           keywords=["paypal", "verify"])

# Avoid: Unstructured strings
logger.info(f"Alert {alert_id} created for {alert_type}")
```

## Log Analysis

### Using jq for JSON Logs
```bash
# Filter by log level
docker-compose logs app | jq 'select(.level == "error")'

# Filter by logger
docker-compose logs app | jq 'select(.logger == "src.fraud_detector")'

# Count alerts by type
docker-compose logs app | jq -r '.alert_type' | sort | uniq -c

# Recent errors
docker-compose logs app --since=1h | jq 'select(.level == "error")'
```

### Log File Analysis
```bash
# View today's logs
tail -f logs/fraud_monitor_$(date +%Y%m%d).log

# Search for specific events
grep "fraud_alert" logs/fraud_monitor_*.log

# Count events by type
jq -r '.event' logs/fraud_monitor_*.log | sort | uniq -c
```

## Performance Considerations

- **Async Logging** - Non-blocking log writes
- **JSON Serialization** - Efficient structured data
- **File Rotation** - Prevents disk space issues
- **Memory Usage** - Minimal overhead

## Troubleshooting

### Logs Not Appearing
- ✅ Check `LOG_LEVEL` environment variable
- ✅ Verify logging configuration is called
- ✅ Check file permissions for logs directory
- ✅ Review Docker container logs

### Sensitive Data in Logs
- ✅ Check security filter patterns
- ✅ Review log message content
- ✅ Update sensitive patterns list
- ✅ Test with sample data

### Performance Issues
- ✅ Monitor log file sizes
- ✅ Check disk space
- ✅ Review log rotation
- ✅ Consider log level adjustment

### Log Analysis Problems
- ✅ Verify JSON format
- ✅ Check jq installation
- ✅ Review log structure
- ✅ Test with sample logs

