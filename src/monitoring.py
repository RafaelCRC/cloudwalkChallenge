from fastapi import FastAPI, HTTPException

import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
# from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import FastAPI, HTTPException
# from fastapi.responses import PlainTextResponse

from .config import settings
from .database import db_manager

# # Prometheus metrics
# from .metrics import MESSAGES_PROCESSED, FRAUD_ALERTS, OCR_PROCESSING_TIME, DATABASE_OPERATIONS, ACTIVE_CONNECTIONS

logger = structlog.get_logger(__name__)

# # Prometheus metrics
# MESSAGES_PROCESSED = Counter('messages_processed_total', 'Total messages processed', ['group_id', 'message_type'])
# FRAUD_ALERTS = Counter('fraud_alerts_total', 'Total fraud alerts generated', ['alert_type'])
# OCR_PROCESSING_TIME = Histogram('ocr_processing_seconds', 'Time spent processing OCR')
# DATABASE_OPERATIONS = Counter('database_operations_total', 'Database operations', ['operation', 'status'])
# ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active database connections')


class HealthChecker:
    """System health monitoring."""
    
    def __init__(self):
        self.last_health_check = datetime.now()
        self.health_status = {}
    
    async def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'components': {}
        }
        
        try:
            # Check database connectivity
            db_health = await self._check_database()
            health_data['components']['database'] = db_health
            
            # Check memory usage
            memory_health = self._check_memory()
            health_data['components']['memory'] = memory_health
            
            # Check recent activity
            activity_health = await self._check_recent_activity()
            health_data['components']['activity'] = activity_health
            
            # Determine overall status
            component_statuses = [comp['status'] for comp in health_data['components'].values()]
            if any(status == 'unhealthy' for status in component_statuses):
                health_data['status'] = 'unhealthy'
            elif any(status == 'degraded' for status in component_statuses):
                health_data['status'] = 'degraded'
            
            self.health_status = health_data
            self.last_health_check = datetime.now()
            
            return health_data
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return {
                'timestamp': datetime.now().isoformat(),
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            
            # Test connection
            async with db_manager.get_connection() as conn:
                await conn.fetchval('SELECT 1')
            
            response_time = time.time() - start_time
            
            status = 'healthy'
            if response_time > 1.0:
                status = 'degraded'
            elif response_time > 5.0:
                status = 'unhealthy'
            
            return {
                'status': status,
                'response_time': response_time,
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            status = 'healthy'
            if memory_percent > 80:
                status = 'degraded'
            elif memory_percent > 95:
                status = 'unhealthy'
            
            return {
                'status': status,
                'memory_percent': memory_percent,
                'available_mb': memory.available // (1024 * 1024),
                'last_check': datetime.now().isoformat()
            }
            
        except ImportError:
            # psutil not available, return basic info
            return {
                'status': 'unknown',
                'error': 'psutil not available',
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error("Memory health check failed", error=str(e))
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    async def _check_recent_activity(self) -> Dict[str, Any]:
        """Check recent system activity."""
        try:
            # Get recent alerts from database
            recent_alerts = await db_manager.get_recent_alerts(hours=1)
            
            status = 'healthy'
            alert_count = len(recent_alerts)
            
            # Too many alerts might indicate issues
            if alert_count > 100:
                status = 'degraded'
            elif alert_count > 1000:
                status = 'unhealthy'
            
            return {
                'status': status,
                'recent_alerts': alert_count,
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Activity health check failed", error=str(e))
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }


class MonitoringAPI:
    """FastAPI application for monitoring endpoints."""
    
    def __init__(self):
        self.app = FastAPI(title="Fraud Monitor API", version="1.0.0")
        self.health_checker = HealthChecker()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup monitoring API routes."""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            health_data = await self.health_checker.check_health()
            
            if health_data['status'] == 'unhealthy':
                raise HTTPException(status_code=503, detail=health_data)
            
            return health_data
        
        # @self.app.get("/metrics")
        # async def metrics():
        #     """Prometheus metrics endpoint."""
        #     return PlainTextResponse(generate_latest())
        
        @self.app.get("/stats")
        async def get_stats():
            """Get system statistics."""
            try:
                recent_alerts = await db_manager.get_recent_alerts(hours=24)
                
                stats = {
                    'timestamp': datetime.now().isoformat(),
                    'alerts_24h': len(recent_alerts),
                    'alert_types': {},
                    'system_status': self.health_checker.health_status.get('status', 'unknown')
                }
                
                # Count alert types
                for alert in recent_alerts:
                    alert_type = alert.get('alert_type', 'unknown')
                    stats['alert_types'][alert_type] = stats['alert_types'].get(alert_type, 0) + 1
                
                return stats
                
            except Exception as e:
                logger.error("Failed to get stats", error=str(e))
                raise HTTPException(status_code=500, detail="Failed to get statistics")


# Global monitoring instances
health_checker = HealthChecker()
monitoring_api = MonitoringAPI()

