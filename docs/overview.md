# 🔍 Fraud Monitor - Quick Overview

A Telegram bot that monitors group chats for fraud and suspicious activities.

## What It Does

- **Monitors Telegram Groups** - Watches multiple group chats simultaneously
- **Detects Fraud Patterns** - Finds credit cards, CVV codes, suspicious terms
- **Scans Images** - Uses OCR to read text from photos and documents
- **Brand Monitoring** - Alerts when financial brands are mentioned
- **Sends Warnings** - Automatically warns groups about suspicious content

## How It Works

```
Telegram Message → Fraud Analysis → Database Storage → Alert Generation
                      ↓
                  OCR Processing (for images)
```

## Alert Types

| Alert Type | Description | Action |
|------------|-------------|---------|
| **🚨 High Risk Fraud** | Brand + suspicious patterns | Critical warning sent |
| **ℹ️ Brand Mention** | Financial brand detected | Info notice sent |
| **⚠️ Suspicious Content** | Fraud patterns without brands | Warning logged |

## Quick Stats

- **Messages Processed**: Real-time monitoring
- **OCR Accuracy**: 60%+ confidence threshold
- **Response Time**: < 1 second per message
- **Storage**: PostgreSQL

## Getting Started

1. **Setup**: `./scripts/setup.sh`
2. **Configure**: Edit `.env` file
3. **Start**: `docker-compose up -d`
4. **Monitor**: `curl localhost:8000/health`

## Key Features

✅ **Security First** - Rate limiting, input validation, audit logging  
✅ **Docker Ready** - Multi-stage builds, health checks included  
✅ **Monitoring** - Prometheus metrics, health endpoints  
✅ **Scalable** - Connection pooling, optimized database  
✅ **Configurable** - Environment-based settings  

## Support

- 📖 **Detailed Docs**: See individual component documentation
- 🔧 **Troubleshooting**: Check application logs
- 📊 **Monitoring**: Use `/health`, `/metrics`, `/stats` endpoints
- 🚨 **Issues**: Review error logs and system status

---
*Built for Application Security Engineers - Secure, reliable, and production-ready.*
