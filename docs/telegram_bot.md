# 🤖 Telegram Bot

Main Telegram bot that monitors groups, processes messages, and sends alerts.

## Overview

The `TelegramMonitor` class handles:

- **Message Collection** - Receives messages from monitored groups
- **Message Processing** - Analyzes text and images for fraud
- **Alert Generation** - Creates and sends fraud alerts
- **Group Management** - Manages multiple monitored groups
- **Error Handling** - Robust error handling and recovery

## Architecture

```
Telegram API → Message Handler → Fraud Analysis → Alert Generation → Group Response
     ↓              ↓                ↓                ↓                ↓
Bot Updates    Text/Image      OCR Processing    Database Storage   Warning Messages
```

## Configuration

### Required Settings
```bash
# Bot token from @BotFather
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Groups to monitor (comma-separated, negative numbers)
TELEGRAM_GROUP_IDS=-1001234567890,-1001234567891
```

### Getting Group IDs
1. **Add bot to group** - Use @BotFather to add your bot
2. **Send test message** - Post any message in the group
3. **Check logs** - Look for group ID in application logs
4. **Use negative number** - Group IDs are negative integers

## Message Processing Flow

### 1. Message Reception
```python
async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    
    # Validate message
    if not self._is_valid_message(message):
        return
    
    # Check if from monitored group
    if message.chat.id not in self.monitored_groups:
        return
    
    # Process message
    await self._process_message(message)
```

### 2. Message Types
| Type | Processing | Description |
|------|------------|-------------|
| **Text** | Direct analysis | Sent to fraud detector |
| **Photo** | OCR + analysis | Extract text, then analyze |
| **Document** | OCR + analysis | Extract text, then analyze |
| **Other** | Logged only | Sticker, video, etc. |

### 3. Processing Pipeline
```python
# Text messages
if message.text:
    await self._process_text_message(message)

# Photo messages  
elif message.photo:
    await self._process_image_message(message)

# Document messages
elif message.document:
    await self._process_document_message(message)
```

## Image Processing

### Photo Messages
```python
async def _process_image_message(self, message, message_id: int, group_id: int):
    # Get largest photo size
    photo = message.photo[-1]
    file = await self.bot.get_file(photo.file_id)
    
    # Download image
    image_bytes = await file.download_as_bytearray()
    
    # Process with OCR
    ocr_result = await ocr_processor.process_image_bytes(bytes(image_bytes))
    
    # Analyze extracted text
    if ocr_result['success']:
        await fraud_detector.analyze_message(
            message_text=ocr_result['text'],
            message_id=message_id,
            group_id=group_id,
            bot=self.bot
        )
```

### Document Messages
```python
async def _process_document_image(self, message, message_id: int, group_id: int):
    document = message.document
    
    # Check if it's an image
    if document.mime_type.startswith('image/'):
        file = await self.bot.get_file(document.file_id)
        document_bytes = await file.download_as_bytearray()
        
        # Process with OCR
        ocr_result = await ocr_processor.process_image_bytes(bytes(document_bytes))
        
        # Analyze extracted text
        if ocr_result['success']:
            await fraud_detector.analyze_message(
                message_text=ocr_result['text'],
                message_id=message_id,
                group_id=group_id,
                bot=self.bot
            )
```

## Alert System

### Alert Types
| Alert Type | Trigger | Action |
|------------|---------|--------|
| **High Risk Fraud** | Brand + suspicious patterns | 🚨 Critical warning sent |
| **Brand Mention** | Brand detected | ℹ️ Info notice sent |
| **Suspicious Content** | Suspicious patterns only | ⚠️ Logged (no message) |

### Sending Alerts
```python
async def send_alert_to_group(self, group_id: int, alert_data: Dict[str, Any]):
    """Send alert message to the originating group."""
    
    alert_type = alert_data['alert_type']
    keywords = alert_data.get('keywords_found', [])
    score = alert_data.get('confidence_score', 0)
    
    if alert_type == "high_risk_fraud":
        message = f"🚨 *FRAUD ALERT* 🚨\n\n"
        message += f"⚠️ High-risk fraud detected!\n"
        message += f"🔍 Keywords: {', '.join(keywords)}\n"
        message += f"📊 Confidence: {score:.1%}\n\n"
        message += f"*Please verify before taking any action.*"
        
    elif alert_type == "brand_mention_info":
        message = f"ℹ️ *Brand Mention Detected*\n\n"
        message += f"🏷️ Brand: {', '.join(keywords)}\n"
        message += f"📊 Confidence: {score:.1%}\n\n"
        message += f"*This is for informational purposes only.*"
    
    # Send message to group
    await self.bot.send_message(
        chat_id=group_id,
        text=message,
        parse_mode='Markdown'
    )
```

## Error Handling

### Connection Errors
```python
try:
    await self.bot.send_message(chat_id=group_id, text=message)
except telegram.error.TelegramError as e:
    logger.error("Failed to send alert", 
                error=str(e), 
                group_id=group_id,
                alert_type=alert_type)
```

### Rate Limiting
```python
# Rate limiter is automatically applied
# No manual rate limiting needed
```

### Message Validation
```python
def _is_valid_message(self, message) -> bool:
    """Validate incoming message."""
    
    # Check if message exists
    if not message:
        return False
    
    # Check if from user (not bot)
    if message.from_user.is_bot:
        return False
    
    # Check if in monitored group
    if message.chat.id not in self.monitored_groups:
        return False
    
    return True
```

## Security Features

### Token Redaction
```python
def redact_bot_token(url: str) -> str:
    """Redact Telegram bot token from URLs."""
    return re.sub(r'bot[^/]+', 'bot[REDACTED]', url)
```

### Input Validation
```python
# All inputs are validated before processing
if not input_validator.validate_message_text(message.text):
    logger.warning("Invalid message text detected")
    return
```

### Rate Limiting
```python
# Rate limiter prevents API abuse
application = Application.builder() \
    .token(settings.telegram_bot_token) \
    .rate_limiter(rate_limiter) \
    .build()
```

## Database Integration

### Message Storage
```python
# Save message to database
message_data = {
    "telegram_message_id": message.message_id,
    "group_id": message.chat.id,
    "user_id": message.from_user.id,
    "username": message.from_user.username,
    "message_text": message.text,
    "message_type": "text"
}

message_id = await db_manager.save_message(message_data)
```

### Image Storage
```python
# Save image and OCR results
image_data = {
    "message_id": message_id,
    "file_id": photo.file_id,
    "ocr_text": ocr_result['text'],
    "ocr_confidence": ocr_result['confidence']
}

image_id = await db_manager.save_image(image_data)
```

## Monitoring & Logging

### Message Processing Logs
```python
logger.info("Message processed",
           message_id=message_id,
           chat_id=message.chat.id,
           message_type=message_data['message_type'])
```

### Error Logs
```python
logger.error("Failed to process message",
            error=str(e),
            message_id=message.message_id,
            chat_id=message.chat.id)
```

### Alert Logs
```python
logger.info("Alert sent to group",
           group_id=group_id,
           alert_type=alert_type,
           keywords=keywords)
```

## Troubleshooting

### Bot Not Responding
- ✅ **Check bot token** - Verify token is correct
- ✅ **Verify bot permissions** - Ensure bot can read messages
- ✅ **Check group membership** - Bot must be in monitored groups
- ✅ **Review logs** - Look for connection errors

### Messages Not Processed
- ✅ **Check group IDs** - Verify negative numbers
- ✅ **Review message validation** - Check validation logic
- ✅ **Monitor error logs** - Look for processing errors
- ✅ **Test with simple messages** - Start with basic text

### Alerts Not Sent
- ✅ **Check alert generation** - Verify fraud detection works
- ✅ **Review bot permissions** - Ensure bot can send messages
- ✅ **Check message formatting** - Verify Markdown syntax
- ✅ **Monitor rate limits** - Check for API limits

### OCR Issues
- ✅ **Check image formats** - Verify supported formats
- ✅ **Review OCR configuration** - Check language settings
- ✅ **Monitor processing times** - Look for timeouts
- ✅ **Test with simple images** - Start with clear text

---

**💡 Pro Tip**: Use the monitoring endpoints (`/health`, `/stats`) to verify the bot is working correctly and processing messages as expected.
