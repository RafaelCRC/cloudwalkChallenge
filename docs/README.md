# 📚 Documentation Index

Welcome to the Fraud Monitor documentation! Here's everything you need to know.

## 🚀 Getting Started

**New to the system?** Start here:

1. **[📖 Overview](overview.md)** - Quick system overview and key concepts
2. **[⚙️ Configuration](config.md)** - Set up your environment and bot settings
3. **[🤖 Telegram Setup](../TELEGRAM_SETUP.md)** - Create bot and configure groups
4. **[🪟 Setup](../SETUP.md)** - Setup instructions

## 📋 Core Documentation

**Understanding the system:**

- **[🗄️ Database](database.md)** - Data storage, tables, and operations
- **[📊 Monitoring](monitoring.md)** - Health checks, metrics, and troubleshooting
- **[🚨 Fraud Detection](fraud_detector.md)** - Fraud analysis and alert generation
- **[🤖 Telegram Bot](telegram_bot.md)** - Message processing and group monitoring
- **[🔍 OCR Processing](ocr.md)** - Image text extraction
- **[🔒 Security](security.md)** - Rate limiting and input validation
- **[📝 Logging](logging_config.md)** - Structured logging and audit trails

## 🔍 Quick Reference

### Common Tasks

| Task | Command | Documentation |
|------|---------|---------------|
| Check system health | `curl localhost:8000/health` | [Monitoring](monitoring.md#health-check) |
| View recent alerts | `curl localhost:8000/stats` | [Monitoring](monitoring.md#statistics) |
| Access database | `docker-compose exec db psql -U fraud_monitor -d fraud_monitoring` | [Database](database.md#maintenance) |
| View logs | `docker-compose logs -f app` | [README](../README.md#troubleshooting) |
| Update configuration | `nano .env` | [Configuration](config.md#quick-setup) |

### Key Files

| File | Purpose |
|------|---------|
| `.env` | Environment configuration |
| `docker-compose.yml` | Service orchestration |
| `requirements.txt` | Python dependencies |
| `src/config.py` | Configuration management |
| `src/fraud_detector.py` | Fraud detection logic |

## 🎯 By Use Case

### **Security Engineer**
- Start with [Overview](overview.md) for system understanding
- Review [Database](database.md) for data structure
- Check [Monitoring](monitoring.md) for observability

### **System Administrator** 
- Focus on [Configuration](config.md) for deployment
- Use [Monitoring](monitoring.md) for system health
- Reference [Database](database.md) for maintenance

### **Developer**
- Read [Overview](overview.md) for architecture
- Study source code in `src/` directory
- Check [Configuration](config.md) for settings

## 🆘 Need Help?

### Troubleshooting Steps
1. **Check Status**: `curl localhost:8000/health`
2. **View Logs**: `docker-compose logs app --tail=50`
3. **Verify Config**: Review your `.env` file
4. **Check Documentation**: Find relevant guide above

### Common Issues
- **Bot not responding**: Check [Telegram Setup](../TELEGRAM_SETUP.md)
- **Database errors**: See [Database](database.md#troubleshooting)
- **Configuration problems**: Review [Configuration](config.md#troubleshooting)
- **System health issues**: Use [Monitoring](monitoring.md#troubleshooting)

## 📊 Documentation Stats

| Document | Purpose | Complexity |
|----------|---------|------------|
| [Overview](overview.md) | Quick introduction | ⭐ Beginner |
| [Configuration](config.md) | Setup guide | ⭐⭐ Easy |
| [Database](database.md) | Data management | ⭐⭐⭐ Intermediate |
| [Monitoring](monitoring.md) | System observability | ⭐⭐ Easy |
| [Fraud Detection](fraud_detector.md) | Core detection logic | ⭐⭐⭐ Intermediate |
| [Telegram Bot](telegram_bot.md) | Message processing | ⭐⭐⭐ Intermediate |
| [OCR Processing](ocr.md) | Image text extraction | ⭐⭐ Easy |
| [Security](security.md) | Security utilities | ⭐⭐⭐ Intermediate |
| [Logging](logging_config.md) | Logging configuration | ⭐⭐ Easy |

---

**💡 Tip**: Bookmark this page for quick access to all documentation!

**🔄 Last Updated**: Documentation refreshed for better readability and user experience.
