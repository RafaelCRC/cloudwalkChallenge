# 🚨 Fraud Detection System

Core fraud detection engine that analyzes messages for suspicious patterns and brand mentions.

## Overview

The `FraudDetector` class is the heart of the fraud monitoring system. It analyzes text content to identify:

- **Brand Mentions** - Financial service brands (PayPal, Visa, etc.)
- **Suspicious Patterns** - Credit cards, CVV codes, phishing terms
- **Risk Scoring** - Calculates confidence levels for alerts
- **Alert Generation** - Creates appropriate alerts based on findings

## How It Works

```
Message Text → Pattern Analysis → Risk Scoring → Alert Generation
     ↓              ↓                ↓              ↓
Brand Detection  Suspicious Terms  Confidence    Database Storage
```

## Detection Patterns

### Brand Keywords
Configured via `BRAND_KEYWORDS` environment variable:
- `visa`, `mastercard`, `paypal`, `stripe`, `amazon`
- Case-insensitive matching
- Partial word matching (e.g., "PayPal" matches "paypal")

### Suspicious Patterns

| Pattern Type | Regex Example | Description |
|--------------|---------------|-------------|
| **Credit Card** | `\b(?:\d{4}[-\s]?){3}\d{4}\b` | 16-digit card numbers |
| **CVV Code** | `\bcvv\s*:?\s*\d{3,4}\b` | CVV/CVC codes |
| **Expiry Date** | `\b(?:exp\|expiry)\s*:?\s*\d{1,2}[\/\-]\d{2,4}\b` | Expiration dates |
| **Bank Account** | `\b(?:account number\|routing number)\s*:?\s*\d+\b` | Account numbers |
| **Fraud Terms** | `\b(?:stolen\|hacked\|leaked\|dump)\b` | Fraud-related keywords |
| **Phishing** | `\b(?:verify account\|update payment)\b` | Phishing attempts |
| **Social Engineering** | `\b(?:urgent\|immediate\|expire)\b` | Urgency tactics |

## Alert Types

### 🚨 High Risk Fraud (`high_risk_fraud`)
- **Trigger**: Brand mention + suspicious patterns
- **Score**: > 0.5
- **Action**: Critical warning sent to group

### ℹ️ Brand Mention (`brand_mention_info`)
- **Trigger**: Brand detected without suspicious patterns
- **Score**: 0.2
- **Action**: Informational notice sent to group

### ⚠️ Suspicious Content (`suspicious_content`)
- **Trigger**: Suspicious patterns without brands
- **Score**: 0.3-0.5
- **Action**: Warning logged (no group message)

## Risk Scoring Algorithm

```python
score = 0.0

# Brand mentions (capped at 2 mentions)
score += min(len(brand_mentions), 2) * 0.2

# Suspicious patterns (capped at 3 patterns)
score += min(len(suspicious_patterns), 3) * 0.3

# Additional factors
if "urgent" in text_lower:
    score += 0.1
if "verify" in text_lower:
    score += 0.1
```

## Usage Examples

### Basic Analysis
```python
from src.fraud_detector import fraud_detector

# Analyze a message
result = await fraud_detector.analyze_message(
    message_text="PayPal verification required - click here",
    message_id=12345,
    group_id=-1001234567890,
    bot=bot_instance
)

print(result['alerts'])  # List of created alerts
print(result['analysis']['suspicious_score'])  # 0.0-1.0
```

### Alert Response
```python
{
    "alerts": [
        {
            "id": 42,
            "type": "high_risk_fraud",
            "score": 0.6,
            "keywords": ["paypal", "verify"]
        }
    ],
    "analysis": {
        "brand_mentions": ["paypal"],
        "suspicious_patterns": ["phishing_terms"],
        "suspicious_score": 0.6,
        "confidence": 0.8
    }
}
```

## Configuration

### Environment Variables
```bash
# Brand keywords to monitor
BRAND_KEYWORDS=visa,mastercard,paypal,stripe,amazon

# Alert cooldown (minutes)
ALERT_COOLDOWN_MINUTES=5
```

### Customizing Detection
```python
# Add custom patterns
fraud_detector.suspicious_patterns[re.compile(r'custom_pattern')] = 'custom_type'

# Modify brand keywords
fraud_detector.brand_keywords.add('new_brand')
```

## Alert Decision Logic

```python
if brand_mentions and suspicious_patterns:
    # High risk: Brand + suspicious content
    alert_type = "high_risk_fraud"
    send_warning = True
elif brand_mentions:
    # Info: Brand mention only
    alert_type = "brand_mention_info" 
    send_warning = True
elif suspicious_patterns and score > 0.3:
    # Warning: Suspicious content
    alert_type = "suspicious_content"
    send_warning = False
```

## Performance Features

- **Pattern Caching** - Compiled regex patterns for speed
- **Score Capping** - Prevents score inflation from spam
- **Async Processing** - Non-blocking analysis
- **Database Integration** - Automatic alert storage

## Security Considerations

- **Input Validation** - All text is sanitized
- **Pattern Limits** - Capped contributions prevent gaming
- **Audit Logging** - All detections are logged
- **Rate Limiting** - Prevents alert spam

## Troubleshooting

### No Alerts Generated
- ✅ Check `BRAND_KEYWORDS` configuration
- ✅ Verify message text is not empty
- ✅ Check score thresholds
- ✅ Review alert cooldown settings

### False Positives
- ✅ Adjust pattern sensitivity
- ✅ Modify brand keyword list
- ✅ Tune score thresholds
- ✅ Review pattern regex accuracy

### Performance Issues
- ✅ Check pattern complexity
- ✅ Monitor database connection
- ✅ Review async processing
- ✅ Check memory usage

---

**💡 Pro Tip**: Use the `/stats` endpoint to monitor detection patterns and adjust thresholds based on real-world data.
