"""Telegram bot for monitoring groups and collecting messages."""

from typing import Optional
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import structlog
import re

from .config import settings
from .database import db_manager
from .ocr import ocr_processor
from .fraud_detector import fraud_detector
from .security import rate_limiter, input_validator

logger = structlog.get_logger(__name__)

def redact_bot_token(url: str) -> str:
    """Redact Telegram bot token from URLs."""
    return re.sub(r'bot[^/]+', 'bot[REDACTED]', url)

class TelegramMonitor:
    """Secure Telegram bot for fraud monitoring."""
    
    def __init__(self):
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None
        self.monitored_groups = set(settings.telegram_groups)
        
    async def initialize(self):
        """Initialize Telegram bot application."""
        try:
            # Create bot application with security settings
            self.application = (
                Application.builder()
                .token(settings.telegram_bot_token)
                .rate_limiter(rate_limiter)
                .build()
            )
            
            self.bot = self.application.bot
            
            # Add message handlers
            self.application.add_handler(
                MessageHandler(
                    filters.ALL & ~filters.COMMAND,
                    self.handle_message
                )
            )
            
            logger.info("Telegram bot initialized", groups=len(self.monitored_groups))
            
        except Exception as e:
            logger.error("Failed to initialize Telegram bot", error=str(e))
            raise
    
    async def start_monitoring(self):
        """Start monitoring Telegram groups."""
        if not self.application:
            raise RuntimeError("Bot not initialized")
        
        try:
            logger.info("Starting Telegram monitoring...")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
            logger.info("Telegram monitoring started successfully")
            
        except Exception as e:
            logger.error("Failed to start Telegram monitoring", error=str(e))
            raise
    
    async def stop_monitoring(self):
        """Stop monitoring and cleanup."""
        if self.application:
            try:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Telegram monitoring stopped")
            except Exception as e:
                logger.error("Error stopping Telegram monitoring", error=str(e))
                
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages with rate limiting."""
        chat_id = update.effective_chat.id if update.effective_chat else "unknown"

        async def callback(update, context):
            return await self._handle_message_logic(update, context)

        try:
            await rate_limiter.process_request(
                callback=callback,
                args=(update, context),
                kwargs={},
                endpoint="handle_message",
                data={"chat_id": chat_id}
            )
        except Exception as e:
            logger.warning(
                "Message blocked by rate limiter",
                chat_id=chat_id,
                error=str(e)
            )
    
    async def _handle_message_logic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages from monitored groups."""
        try:
            message = update.effective_message
            chat = update.effective_chat
            user = update.effective_user
            
            # Security: Only process messages from monitored groups
            if chat.id not in self.monitored_groups:
                return
            
            # Security: Validate input
            if not input_validator.validate_message(message):
                logger.warning("Invalid message format", chat_id=chat.id)
                return
            
            # Extract message data
            message_data = {
                'telegram_message_id': message.message_id,
                'group_id': chat.id,
                'user_id': user.id if user else None,
                'username': user.username if user else None,
                'message_text': message.text or message.caption or '',
                'message_type': self._get_message_type(message)
            }
            
            # Save message to database
            message_id = await db_manager.save_message(message_data)   
            
            # Process text content for fraud detection
            if message_data['message_text']:
                await self._analyze_text_content(message_data['message_text'], message_id, chat.id)
            
            # Process images if present
            if message.photo:
                await self._process_image_message(message, message_id, chat.id)
            elif message.document and self._is_image_document(message.document):
                await self._process_document_image(message, message_id, chat.id)
            
            logger.debug(
                "Message processed",
                message_id=message_id,
                chat_id=chat.id,
                message_type=message_data['message_type']
            )
            
        except Exception as e:
            logger.error("Error handling message", error=str(e), chat_id=chat.id if chat else None)
        
    def _get_message_type(self, message) -> str:
        """Determine message type."""
        if message.photo:
            return 'photo'
        elif message.document:
            return 'document'
        elif message.video:
            return 'video'
        elif message.text:
            return 'text'
        elif message.caption:
            return 'caption'
        else:
            return 'other'
    
    def _is_image_document(self, document) -> bool:
        """Check if document is an image."""
        if not document.mime_type:
            return False
        return document.mime_type.startswith('image/')
    
    async def _analyze_text_content(self, text: str, message_id: int, group_id: int):
        """Analyze text content for fraud indicators."""
        try:
            analysis_result = await fraud_detector.analyze_message(text, message_id, group_id, self.bot)
            
            if analysis_result['alerts']:
                logger.info(
                    "Fraud alerts generated",
                    message_id=message_id,
                    alert_count=len(analysis_result['alerts'])
                )
                
        except Exception as e:
            logger.error("Text analysis failed", error=str(e), message_id=message_id)
    
    async def _process_image_message(self, message, message_id: int, group_id: int):
        """Process image message with OCR."""
        try:
            # Get the largest photo size
            photo = message.photo[-1]
            
            # Security: Check file size
            if photo.file_size and photo.file_size > 10 * 1024 * 1024:  # 10MB limit
                logger.warning("Image too large, skipping", file_size=photo.file_size)
                return
            
            # Download image
            file = await self.bot.get_file(photo.file_id)
            image_bytes = await file.download_as_bytearray()
            
            ocr_result = await ocr_processor.process_image_bytes(bytes(image_bytes))
            
            # Save image data
            image_data = {
                'message_id': message_id,
                'file_id': photo.file_id,
                'file_path': None,
                'ocr_text': ocr_result.get('text', ''),
                'ocr_confidence': ocr_result.get('confidence', 0)
            }
            
            image_id = await db_manager.save_image(image_data)
            
            # Analyze OCR text for fraud
            if ocr_result.get('text'):
                await self._analyze_text_content(ocr_result['text'], message_id, group_id)
            
            logger.info(
                "Image processed",
                image_id=image_id,
                ocr_success=ocr_result.get('success', False),
                text_length=len(ocr_result.get('text', ''))
            )
            
        except Exception as e:
            logger.error("Image processing failed", error=str(e), message_id=message_id)
    
    async def _process_document_image(self, message, message_id: int, group_id: int):
        """Process document if it's an image."""
        try:
            document = message.document
            
            # Security checks
            if document.file_size > 10 * 1024 * 1024:  # 10MB limit
                logger.warning("Document too large, skipping", file_size=document.file_size)
                return
            
            # Download document
            file = await self.bot.get_file(document.file_id)
            document_bytes = await file.download_as_bytearray()
            
            # Process with OCR
            ocr_result = await ocr_processor.process_image_bytes(bytes(document_bytes))
                        
            # Save image data
            image_data = {
                'message_id': message_id,
                'file_id': document.file_id,
                'file_path': document.file_name,
                'ocr_text': ocr_result.get('text', ''),
                'ocr_confidence': ocr_result.get('confidence', 0)
            }
            
            image_id = await db_manager.save_image(image_data)
            
            # Analyze OCR text for fraud
            if ocr_result.get('text'):
                await self._analyze_text_content(ocr_result['text'], message_id, group_id)
            
            logger.info(
                "Document image processed",
                image_id=image_id,
                filename=document.file_name,
                ocr_success=ocr_result.get('success', False)
            )
            
        except Exception as e:
            logger.error("Document image processing failed", error=str(e), message_id=message_id)


# Global Telegram monitor instance
telegram_monitor = TelegramMonitor()

