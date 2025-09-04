"""Database models and connection management."""

import asyncpg
from typing import Optional, List, Dict, Any
import structlog
from contextlib import asynccontextmanager

from .config import settings

logger = structlog.get_logger(__name__)

class DatabaseManager:
    """Secure database connection manager."""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """Initialize database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                settings.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60,
                server_settings={
                    'jit': 'off',  # Security: Disable JIT compilation
                }
            )
            logger.info("Database pool initialized")
            await self._create_tables()
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            raise
    
    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool."""
        if not self.pool:
            raise RuntimeError("Database not initialized")
        
        async with self.pool.acquire() as conn:
            yield conn
    
    async def _create_tables(self):
        """Create database tables if they don't exist."""
        async with self.get_connection() as conn:
            # Messages table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
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
            """)
            
            # Images table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    id SERIAL PRIMARY KEY,
                    message_id INTEGER REFERENCES messages(id) ON DELETE CASCADE,
                    file_id VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500),
                    ocr_text TEXT,
                    ocr_confidence FLOAT,
                    processed_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Alerts table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    message_id INTEGER REFERENCES messages(id) ON DELETE CASCADE,
                    alert_type VARCHAR(100) NOT NULL,
                    keywords_found TEXT[],
                    confidence_score FLOAT,
                    status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    notified_at TIMESTAMP WITH TIME ZONE
                );
            """)
            
            # Create indexes for performance
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_group_id ON messages(group_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);")
            
            logger.info("Database tables created/verified")
    
    async def save_message(self, message_data: Dict[str, Any]) -> int:
        """Save telegram message to database."""
        async with self.get_connection() as conn:
            try:
                query = """
                    INSERT INTO messages (telegram_message_id, group_id, user_id, username, 
                                        message_text, message_type)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (telegram_message_id, group_id) 
                    DO UPDATE SET processed_at = NOW()
                    RETURNING id;
                """
                
                result = await conn.fetchval(
                    query,
                    message_data["telegram_message_id"],
                    message_data["group_id"],
                    message_data.get("user_id"),
                    message_data.get("username"),
                    message_data.get("message_text"),
                    message_data["message_type"]
                )
                
                logger.debug("Message saved", message_id=result, group_id=message_data["group_id"])
                return result
                
            except Exception as e:
                logger.error("Failed to save message", error=str(e))
                raise
    
    async def save_image(self, image_data: Dict[str, Any]) -> int:
        """Save image data to database."""
        async with self.get_connection() as conn:
            try:
                query = """
                    INSERT INTO images (message_id, file_id, file_path, ocr_text, 
                                      ocr_confidence, processed_at)
                    VALUES ($1, $2, $3, $4, $5, NOW())
                    RETURNING id;
                """
                
                result = await conn.fetchval(
                    query,
                    image_data["message_id"],
                    image_data["file_id"],
                    image_data.get("file_path"),
                    image_data.get("ocr_text"),
                    image_data.get("ocr_confidence")
                )
                
                logger.debug("Image saved", image_id=result)
                return result
                
            except Exception as e:
                logger.error("Failed to save image", error=str(e))
                raise
    
    async def create_alert(self, alert_data: Dict[str, Any]) -> int:
        """Create fraud alert."""
        async with self.get_connection() as conn:
            try:
                query = """
                    INSERT INTO alerts (message_id, alert_type, keywords_found, 
                                      confidence_score, status)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id;
                """
                
                result = await conn.fetchval(
                    query,
                    alert_data["message_id"],
                    alert_data["alert_type"],
                    alert_data.get("keywords_found", []),
                    alert_data.get("confidence_score", 0.0),
                    alert_data.get("status", "pending")
                )
                
                logger.debug("Alert created", alert_id=result, type=alert_data["alert_type"])
                return result
                
            except Exception as e:
                logger.error("Failed to create alert", error=str(e))
                raise
    
    async def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts for monitoring."""
        async with self.get_connection() as conn:
            try:
                query = """
                    SELECT a.*, m.group_id, m.username, m.message_text
                    FROM alerts a
                    JOIN messages m ON a.message_id = m.id
                    WHERE a.created_at > NOW() - ($1 || ' hours')::INTERVAL
                    ORDER BY a.created_at DESC
                    LIMIT 100;
                """
                
                rows = await conn.fetch(query, str(hours))
                return [dict(row) for row in rows]
                
            except Exception as e:
                logger.error("Failed to get recent alerts", error=str(e))
                return []


# Global database manager instance
db_manager = DatabaseManager()

