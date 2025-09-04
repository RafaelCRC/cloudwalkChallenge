# Telegram Setup Guide

## 🤖 **Step 1: Create Your Telegram Bot**

### 1.1 Create the Bot
1. Open Telegram and search for `@BotFather`
2. Start a chat and send `/newbot`
3. Choose a name: `Fraud Monitor Bot`
4. Choose username: `your_fraud_monitor_bot` (must be unique)
5. **Copy the bot token** (looks like: `1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ`)

### 1.2 Configure Bot Settings
Send these commands to @BotFather:

```
/setprivacy
Choose your bot → Disable

/setjoingroups  
Choose your bot → Enable

## 📱 **Step 2: Set Up Test Groups**

### 2.1 Create Test Groups
1. **Create a new group** in Telegram
2. **Name it**: "Fraud Test Group"
3. **Add your bot** to the group
4. **Make the bot an admin** (or ensure it can read messages)

### 2.2 Get Group IDs
1. **Send a message** in your test group
2. **Visit**: `https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates`
3. **Look for** `"chat":{"id":-1001234567890` (negative number)
4. **Copy the negative number** (that's your group ID)

### 2.3 Update Configuration
Edit your `.env` file:
```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_GROUP_IDS=-1001234567890,-1001987654321
```

## 🧪 **Step 3: Test the System**

### 3.1 Start the System
```bash
# Start all services
docker-compose up -d

# Check if running
docker-compose ps

# Watch logs
docker-compose logs -f app
```

### 3.2 Test Message Detection

#### Send Test Messages in Your Group:

**Legitimate Messages** (should have low risk scores):
```
Hello everyone! How's your day?
Meeting at 3 PM today
Weather is nice outside
```

**Brand Mentions** (should detect keywords):
```
I used my Visa card today
PayPal payment went through
Mastercard has good rewards
```

**Suspicious Content** (should generate alerts):
```
Urgent! Verify your account now
Click here to update payment
Your card expires soon
```

### 3.3 Test Image OCR

Create test images with text and send them to your group:

**Credit Card Image**: Create an image with text like:
```
VISA
4532 1234 5678 9012
VALID THRU 12/25
CVV: 123
```

**Phishing Image**: Create an image with:
```
URGENT: Verify PayPal Account
Click here immediately
Account will be suspended
```

## 📊 **Step 4: Monitor Results**

### 4.1 Check System Health
```bash
curl http://localhost:8000/health
```

### 4.2 View Statistics
```bash
curl http://localhost:8000/stats
```

### 4.3 Check Database
```bash
# Connect to database
docker-compose exec db psql -U fraud_monitor -d fraud_monitoring

# Check messages
SELECT COUNT(*) FROM messages;

# Check alerts
SELECT alert_type, COUNT(*) FROM alerts GROUP BY alert_type;

# View recent alerts
SELECT * FROM alerts ORDER BY created_at DESC LIMIT 10;
```

### 4.4 Monitor Logs
```bash
# Application logs
docker-compose logs -f app

# Filter for alerts
docker-compose logs app | grep "Fraud alert"

# Filter for OCR processing
docker-compose logs app | grep "OCR"
```

## 🔍 **Step 5: Understanding the Output**

### Log Messages You Should See:

**Bot Started Successfully:**
```
INFO: Telegram bot initialized groups=1
INFO: Telegram monitoring started successfully
```

**Message Processing:**
```
INFO: Message processed message_id=123 chat_id=-1001234567890 message_type=text
```

**Fraud Detection:**
```
WARNING: Fraud alert generated alert_type=high_risk_fraud confidence=0.85
```

**OCR Processing:**
```
INFO: OCR processing completed text_length=45 confidence=87.3
INFO: Image processed image_id=456 ocr_success=True
```

### Database Tables:

**Messages Table:**
- Stores all Telegram messages
- Links to images and alerts

**Images Table:**
- Stores OCR results
- Links extracted text to messages

**Alerts Table:**
- Fraud detection results
- Confidence scores and keywords

## 📈 **Expected Results**

After sending test messages, you should see:

1. **Messages stored** in the database
2. **Brand mentions detected** for keywords like "visa", "paypal"
3. **Fraud alerts generated** for suspicious patterns
4. **OCR text extracted** from images
5. **High confidence scores** for obvious fraud attempts
6. **Low scores** for legitimate messages

### Sample Alert Output:
```json
{
  "id": 123,
  "type": "high_risk_fraud",
  "score": 0.85,
  "keywords": ["visa", "cvv", "stolen"]
}
```

