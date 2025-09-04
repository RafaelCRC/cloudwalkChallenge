# Deployment Guide

## Quick Deployment Steps

### 1. Prerequisites Check
```bash
# Verify Docker is installed
docker --version
docker-compose --version

# Verify you have a Telegram bot token
# Get one from @BotFather on Telegram
```

### 2. Initial Setup
```bash
# Clone and enter directory
cd cloudwalk-challenge

# Run setup script (generates secure keys)
./scripts/setup.sh

# Or manually copy and edit environment
cp env.example .env
nano .env
```

### 3. Configure Telegram
```bash
# Edit .env file and set:
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_GROUP_IDS=-1001234567890,-1001234567891

# To get group IDs:
# 1. Add your bot to target groups
# 2. Send a message in each group  
# 3. Check logs after starting the bot
```

### 4. Start Services
```bash
# Build and start all services
docker-compose up -d

# Check if services are running
docker-compose ps

# View logs
docker-compose logs -f app
```

### 5. Verify Deployment
```bash
# Check application health
curl http://localhost:8000/health

# View metrics
curl http://localhost:8000/metrics

# Check database
docker-compose exec db psql -U fraud_monitor -d fraud_monitoring -c "SELECT COUNT(*) FROM messages;"
```

## Security Checklist

- [ ] Strong passwords generated for database
- [ ] Secret keys are random and secure  
- [ ] `.env` file is not committed to version control
- [ ] Bot token is kept secure
- [ ] Database access is restricted
- [ ] Logs don't contain sensitive information
- [ ] Rate limiting is configured
- [ ] Input validation is active

## Production Considerations

### Environment Variables
```bash
# Production settings
LOG_LEVEL=WARNING
RATE_LIMIT_REQUESTS=50
```

### Resource Limits
```yaml
# Add to docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

### Backup Strategy
```bash
# Database backup
docker-compose exec db pg_dump -U fraud_monitor fraud_monitoring > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T db psql -U fraud_monitor fraud_monitoring < backup_20231201.sql
```

### Monitoring Setup
```bash
# External monitoring endpoints
GET /health    # Health check
GET /metrics   # Prometheus metrics  
GET /stats     # System statistics
```

## Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check logs
docker-compose logs

# Rebuild images
docker-compose build --no-cache
docker-compose up -d
```

**Database connection errors:**
```bash
# Check database status
docker-compose exec db pg_isready -U fraud_monitor

# Reset database
docker-compose down -v
docker-compose up -d
```

**Bot not receiving messages:**
```bash
# Verify bot token
docker-compose logs app | grep "bot"

# Check group permissions
# Bot must be admin or have message access
```

**High resource usage:**
```bash
# Monitor resources
docker stats

# Adjust limits in docker-compose.yml
# Clean old data
docker-compose exec db psql -U fraud_monitor -d fraud_monitoring -c "SELECT cleanup_old_data();"
```

## Maintenance

### Regular Tasks
```bash
# Weekly: Clean old logs
find logs/ -name "*.log" -mtime +7 -delete

# Monthly: Database maintenance
docker-compose exec db psql -U fraud_monitor -d fraud_monitoring -c "VACUUM ANALYZE;"

# As needed: Update dependencies
docker-compose pull
docker-compose build --no-cache
docker-compose up -d
```

### Log Management
```bash
# View recent alerts
docker-compose logs app | grep "Fraud alert"

# Monitor performance
docker-compose logs app | grep "processing_time"

# Security events
docker-compose logs app | grep "security_event"
```

## Scaling

### Horizontal Scaling
```bash
# Scale application instances
docker-compose up -d --scale app=3

# Load balancer needed for multiple instances
```

### Database Optimization
```sql
-- Monitor slow queries
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

-- Index usage
SELECT schemaname, tablename, attname, n_distinct, correlation FROM pg_stats;
```

## Security Hardening

### Additional Security Measures
```bash
# Use secrets management
docker secret create db_password /path/to/password/file

# Network isolation
docker network create --driver bridge fraud_monitor_net

# Regular security updates
docker-compose pull
docker-compose up -d
```

### Audit Configuration
```bash
# Enable audit logging
echo "AUDIT_ENABLED=true" >> .env

# Review audit logs
docker-compose logs app | grep "audit"
```

---

**Note**: This system handles sensitive fraud detection data. Ensure all security measures are properly implemented before production deployment.

