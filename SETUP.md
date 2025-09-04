# Setup Guide

## 🚀 **Quick Start**

### Prerequisites
- Docker
- Telegram account
- Text editor (VS Code, Notepad++, etc.)

### Step 1: Create Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Send**: `/newbot`
3. **Name your bot**: `Fraud Monitor Bot`
4. **Username**: `your_fraud_monitor_bot` (must be unique)
5. **Copy the token**: `1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ`

### Step 2: Configure Bot Settings
Send to @BotFather:
```
/setprivacy
[Choose your bot] → Disable

/setjoingroups  
[Choose your bot] → Enable
```

### Step 3: Set Up Test Group
1. **Create a new group** in Telegram
2. **Name it**: "Fraud Test Group"
3. **Add your bot** to the group
4. **Make bot admin** (or ensure it can read messages)

### Step 4: Get Group ID

#### Method 1: Manual
1. **Send a message** in your test group
2. **Open browser** and go to:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
3. **Look for**: `"chat":{"id":-1001234567890`
4. **Copy the negative number** (that's your group ID)


### Step 5: run setup.sh

1. **run setup.sh**:
   ```bash
   ./setup.sh
   ```

2. **Edit `.env` file** with your favorite text editor:
   ```
   TELEGRAM_BOT_TOKEN=your_actual_bot_token_here
   TELEGRAM_GROUP_IDS=-1001234567890
   ```

### Step 6: Start the System

```bash
# Build and start all services
docker-compose up -d

# Check if services are running
docker-compose ps

# View logs
docker-compose logs -f app
```

### Step 7: Test the System

#### Test Health Check
Open browser or use bash:
```bash
# Using bash
curl http://localhost:8000/health

# Or open in browser
# http://localhost:8000/health
```

#### Send Test Messages in Your Telegram Group

**Normal Messages:**
```
Hello everyone!
How's your day going?
```

**Brand Mentions:**
```
I used PayPal today
My Visa card works great
Stripe payment processed
```

**Suspicious Content:**
```
Urgent! Verify your account
Click here to update payment
Account will be suspended
```

**High-Risk Fraud:**
```
Selling credit card data
CVV codes available
Hacked accounts for sale
```

#### Test Images
Create simple images with text and send them:
- Screenshot of fake credit card
- Image with "URGENT: Verify PayPal"
- Normal text image

### Step 8: Monitor Results

#### Check Logs
```bash
# View application logs
docker-compose logs app

# Filter for alerts 
docker-compose logs app | Select-String "alert"

# Filter for OCR processing
docker-compose logs app | Select-String "OCR"
```

#### Check Database
```bash
# Connect to database
docker-compose exec db psql -U fraud_monitor -d fraud_monitoring

# Inside database, run:
# SELECT COUNT(*) FROM messages;
# SELECT * FROM alerts ORDER BY created_at DESC LIMIT 5;
```

#### View Statistics
```bash
# Get system stats
curl http://localhost:8000/stats

# Or open in browser
# http://localhost:8000/stats
```

## 🔧 **Commands**
```bash
# Check Docker status
docker version
docker-compose version

# View running containers
docker ps

# Stop services
docker-compose down

# Rebuild after changes
docker-compose build --no-cache
docker-compose up -d

# View logs with timestamp
docker-compose logs -f -t app

# Clean up old containers
docker system prune
```

## ✅ **Expected Results**

After setup, you should see:

1. **Healthy system**: `http://localhost:8000/health` returns success
2. **Messages processed**: Logs show incoming Telegram messages
3. **Fraud alerts**: Suspicious messages generate alerts
4. **OCR working**: Images processed and text extracted
5. **Database populated**: Messages and alerts stored

### Sample Log Output:
```
INFO: Telegram bot initialized groups=1
INFO: Message processed message_id=123 chat_id=-1001234567890
WARNING: Fraud alert generated alert_type=high_risk_fraud confidence=0.85
INFO: OCR processing completed text_length=45 confidence=87.3
```

## 📞 **Need Help?**

1. **Check logs**: `docker-compose logs -f app`
2. **Verify configuration**: Check your `.env` file
3. **Test bot token**: Visit `https://api.telegram.org/bot<TOKEN>/getMe`
4. **Check group access**: Ensure bot is admin in test group
5. **Restart services**: `docker-compose restart`

Your fraud monitoring system should now be running and detecting suspicious activities in your Telegram groups!

