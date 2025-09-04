# 🗄️ Database Documentation

Simple guide to the PostgreSQL database used by the fraud monitoring system.

## Quick Overview

The system uses **PostgreSQL** to store:
- 💬 **Messages** from Telegram groups
- 🖼️ **Images** and OCR results  
- 🚨 **Alerts** from fraud detection
- 📋 **Audit logs** for security

## Database Tables

### 1. Messages (`messages`)
Stores all Telegram messages.

```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    telegram_message_id BIGINT NOT NULL,
    group_id BIGINT NOT NULL,
    user_id BIGINT,
    username VARCHAR(255),
    message_text TEXT,
    message_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(telegram_message_id, group_id)
);
```

**Key Fields:**
- `telegram_message_id` - Telegram's message ID
- `group_id` - Group chat ID (negative number)
- `message_text` - Full message content
- `message_type` - `text`, `photo`, `document`, etc.

### 2. Images (`images`)
Stores image data and OCR results.

```sql
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    message_id INTEGER REFERENCES messages(id),
    file_id VARCHAR(255) NOT NULL,
    ocr_text TEXT,
    ocr_confidence FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Key Fields:**
- `message_id` - Links to parent message
- `file_id` - Telegram file identifier
- `ocr_text` - Text extracted from image
- `ocr_confidence` - OCR accuracy (0-100%)

### 3. Alerts (`alerts`)
Stores fraud detection results.

```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    message_id INTEGER REFERENCES messages(id),
    alert_type VARCHAR(100) NOT NULL,
    keywords_found TEXT[],
    confidence_score FLOAT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Alert Types:**
- `high_risk_fraud` - Critical fraud detected
- `brand_mention_info` - Brand name found
- `suspicious_content` - Suspicious patterns
- `fraud_detection` - General fraud alert

## Common Database Operations

### Using the DatabaseManager

```python
from src.database import db_manager

# Save a message
message_id = await db_manager.save_message({
    "telegram_message_id": 12345,
    "group_id": -1001234567890,
    "message_text": "Hello world",
    "message_type": "text"
})

# Save OCR results
image_id = await db_manager.save_image({
    "message_id": message_id,
    "file_id": "BAADBAADrQADBREAAYag2ej2gfshAg",
    "ocr_text": "PayPal verification required",
    "ocr_confidence": 95.5
})

# Create an alert
alert_id = await db_manager.create_alert({
    "message_id": message_id,
    "alert_type": "brand_mention_info",
    "keywords_found": ["paypal"],
    "confidence_score": 0.8
})

# Get recent alerts
alerts = await db_manager.get_recent_alerts(hours=24)
```

## Configuration

Set these environment variables:

```bash
DATABASE_URL=postgresql://fraud_monitor:password@localhost:5432/fraud_monitoring
DB_PASSWORD=your_secure_password
```

## Maintenance

### View Data
```bash
# Access database
docker-compose exec db psql -U fraud_monitor -d fraud_monitoring

# Check recent activity
SELECT alert_type, COUNT(*) FROM alerts 
WHERE created_at > NOW() - INTERVAL '24 hours' 
GROUP BY alert_type;

# View latest messages
SELECT * FROM messages ORDER BY created_at DESC LIMIT 10;
```

### Backup & Restore
```bash
# Backup
docker-compose exec db pg_dump -U fraud_monitor fraud_monitoring > backup.sql

# Restore
docker-compose exec -T db psql -U fraud_monitor fraud_monitoring < backup.sql
```

## Performance Features

- **Connection Pooling** - 2-10 concurrent connections
- **Indexes** - Optimized for time-based queries
- **Constraints** - Prevents duplicate messages
- **Cascading Deletes** - Automatic cleanup

## Security

- ✅ **Row Level Security** enabled
- ✅ **Limited user privileges**
- ✅ **Input validation** on all operations
- ✅ **Audit logging** for all changes
- ✅ **Connection timeouts** prevent hanging

---

**💡 Tip**: Use the monitoring endpoints (`/stats`) to view database activity without direct SQL access.