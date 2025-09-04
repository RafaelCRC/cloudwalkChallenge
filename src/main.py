"""Main application entry point."""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager

from .logging_config import configure_logging
configure_logging()

import structlog
import uvicorn

from .config import settings
from .logging_config import configure_logging, audit_logger
from .database import db_manager
from .telegram_bot import telegram_monitor
from .monitoring import monitoring_api, health_checker

logger = structlog.get_logger(__name__)


class FraudMonitorApp:
    """Main fraud monitoring application."""
    
    def __init__(self):
        self.running = False
        self.tasks = []
    
    async def initialize(self):
        """Initialize all components."""
        try:
            logger.info("Initializing Fraud Monitor Application")
            
            # Initialize database
            await db_manager.initialize()
            
            # Initialize Telegram bot
            await telegram_monitor.initialize()
            
            logger.info("All components initialized successfully")
            audit_logger.log_security_event("application_start", {"status": "success"})
            
        except Exception as e:
            logger.error("Failed to initialize application", error=str(e))
            audit_logger.log_security_event("application_start", {"status": "failed", "error": str(e)})
            raise
    
    async def start(self):
        """Start the application."""
        try:
            self.running = True
            
            # Start Telegram monitoring
            telegram_task = asyncio.create_task(telegram_monitor.start_monitoring())
            self.tasks.append(telegram_task)
            
            # Start health checker
            health_task = asyncio.create_task(self._health_check_loop())
            self.tasks.append(health_task)
            
            logger.info("Fraud monitoring application started")
            
            # Wait for tasks to complete
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error("Application error", error=str(e))
            audit_logger.log_security_event("application_error", {"error": str(e)})
            raise
    
    async def stop(self):
        """Stop the application gracefully."""
        try:
            logger.info("Stopping fraud monitoring application")
            self.running = False
            
            # Cancel all tasks
            for task in self.tasks:
                task.cancel()
            
            # Stop components
            await telegram_monitor.stop_monitoring()
            await db_manager.close()
            
            logger.info("Application stopped successfully")
            audit_logger.log_security_event("application_stop", {"status": "success"})
            
        except Exception as e:
            logger.error("Error stopping application", error=str(e))
            audit_logger.log_security_event("application_stop", {"status": "failed", "error": str(e)})
    
    async def _health_check_loop(self):
        """Periodic health check loop."""
        while self.running:
            try:
                await health_checker.check_health()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Health check error", error=str(e))
                await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app):
    """FastAPI lifespan context manager."""
    # Startup
    fraud_app = FraudMonitorApp()
    await fraud_app.initialize()
    
    # Start background task
    task = asyncio.create_task(fraud_app.start())
    
    try:
        yield
    finally:
        # Shutdown
        await fraud_app.stop()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


def setup_signal_handlers(fraud_app: FraudMonitorApp):
    """Setup signal handlers for graceful shutdown."""
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        asyncio.create_task(fraud_app.stop())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def run_standalone():
    """Run the application in standalone mode."""
    # Configure logging
    configure_logging()
    
    # Create and run application
    fraud_app = FraudMonitorApp()
    setup_signal_handlers(fraud_app)
    
    try:
        await fraud_app.initialize()
        await fraud_app.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        await fraud_app.stop()


def run_with_api():
    """Run the application with monitoring API."""
    # Configure logging
    configure_logging()
    
    # Setup FastAPI app with lifespan
    app = monitoring_api.app
    app.router.lifespan_context = lifespan
    
    # Run with uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=None,  # Use our custom logging
        access_log=False
    )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--api":
        run_with_api()
    else:
        asyncio.run(run_standalone())

