# 📊 Monitoring & Health Checks

Simple guide to monitoring the fraud detection system.

## Quick Status Check

```bash
# Is everything working?
curl http://localhost:8000/health

# What's happening?
curl http://localhost:8000/stats

# Get metrics for Prometheus
curl http://localhost:8000/metrics
```

## API Endpoints

### 🏥 Health Check - `GET /health`

**Purpose**: Check if all system components are working

**Response Example**:
```json
{
  "timestamp": "2025-01-04T12:00:00.000000",
  "status": "healthy",
  "components": {
    "database": {"status": "healthy", "response_time": 0.123},
    "memory": {"status": "healthy", "memory_percent": 65.4},
    "activity": {"status": "healthy", "recent_alerts": 45}
  }
}
```

**Status Levels**:
- 🟢 **healthy** - Everything working normally
- 🟡 **degraded** - Some performance issues
- 🔴 **unhealthy** - Critical problems need attention

**Quick Check**:
```bash
# Just get the status
curl -s http://localhost:8000/health | jq '.status'

# Monitor in a loop
watch -n 30 'curl -s http://localhost:8000/health | jq ".status"'
```

### 📈 Statistics - `GET /stats`

**Purpose**: Get system activity summary

**Response Example**:
```json
{
  "timestamp": "2025-01-04T12:00:00.000000",
  "alerts_24h": 156,
  "alert_types": {
    "brand_mention_info": 89,
    "high_risk_fraud": 12,
    "suspicious_content": 34
  },
  "system_status": "healthy"
}
```

**Quick Usage**:
```bash
# How many alerts today?
curl -s http://localhost:8000/stats | jq '.alerts_24h'

# What types of alerts?
curl -s http://localhost:8000/stats | jq '.alert_types'
```

### 📊 Metrics - `GET /metrics`

**Purpose**: Prometheus-compatible metrics for monitoring tools

**Key Metrics**:
- `messages_processed_total` - Messages handled
- `fraud_alerts_total` - Alerts generated  
- `ocr_processing_seconds` - OCR performance
- `database_operations_total` - Database activity

## Health Check Components

### Database Health
- **Healthy**: Response < 1 second
- **Degraded**: Response 1-5 seconds
- **Unhealthy**: Response > 5 seconds or connection failed

### Memory Health  
- **Healthy**: Usage < 80%
- **Degraded**: Usage 80-95%
- **Unhealthy**: Usage > 95%

### Activity Health
- **Healthy**: < 100 alerts/hour
- **Degraded**: 100-1000 alerts/hour  
- **Unhealthy**: > 1000 alerts/hour

## Using with Monitoring Tools

### Docker Health Checks
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

