"""Fraud detection and brand mention analysis."""

import re
from typing import List, Dict, Any, Set, Optional
import structlog

from .config import settings
from .database import db_manager

logger = structlog.get_logger(__name__)


class FraudDetector:
    """Advanced fraud detection system with brand mention analysis."""
    
    def __init__(self):
        self.brand_keywords = set(kw.lower() for kw in settings.keywords_list)
        self.suspicious_patterns = self._compile_suspicious_patterns()
    
    def _compile_suspicious_patterns(self) -> Dict[re.Pattern, str]:
        """Compile regex patterns mapped to their descriptions."""
        pattern_map = {
            re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b', re.IGNORECASE): 'credit_card_number',
            re.compile(r'\bcvv\s*:?\s*\d{3,4}\b', re.IGNORECASE): 'cvv_code',
            re.compile(r'\b(?:exp|expiry|expires?)\s*:?\s*\d{1,2}[\/\-]\d{2,4}\b', re.IGNORECASE): 'expiry_date',
            re.compile(r'\b(?:account\s+number|routing\s+number|iban|swift)\s*:?\s*\d+\b', re.IGNORECASE): 'bank_account',
            re.compile(r'\b(?:stolen|hacked|leaked|dump|fullz|cc|cvv2)\b', re.IGNORECASE): 'fraud_terms',
            re.compile(r'\b(?:verify\s+account|update\s+payment|suspended\s+account)\b', re.IGNORECASE): 'phishing_terms',
            re.compile(r'\b(?:urgent|immediate|expire|suspend|verify|click\s+here)\b', re.IGNORECASE): 'social_engineering'
        }
        return pattern_map
    
    async def analyze_message(self, message_text: str, message_id: int, group_id: int = None, bot = None) -> Dict[str, Any]:
        """Analyze message for fraud indicators and brand mentions."""

        if not message_text:
            return {'alerts': [], 'analysis': {'brand_mentions': [], 'suspicious_score': 0}}
        
        try:
            analysis = {
                'brand_mentions': [],
                'suspicious_patterns': [],
                'suspicious_score': 0,
                'confidence': 0.0
            }
            
            text_lower = message_text.lower()
            
            # Check for brand mentions
            brand_mentions = self._detect_brand_mentions(text_lower)
            analysis['brand_mentions'] = brand_mentions
            
            # Check for suspicious patterns
            suspicious_patterns = self._detect_suspicious_patterns(message_text)
            analysis['suspicious_patterns'] = suspicious_patterns
            
            # Calculate suspicious score
            score = self._calculate_suspicious_score(brand_mentions, suspicious_patterns, text_lower)
            analysis['suspicious_score'] = score
            
            # Generate alerts if necessary
            alerts = []
            
            logger.info(
                "Alert decision logic",
                message_id=message_id,
                score=score,
                brand_mentions=brand_mentions,
                suspicious_patterns=suspicious_patterns,
                high_risk_condition=score > 0.6 or (brand_mentions and suspicious_patterns),
                brand_info_condition=brand_mentions and not suspicious_patterns
            )
            
            # High-risk fraud alerts (critical warnings)
            if score > 0.6 or (brand_mentions and suspicious_patterns):
                alert_data = await self._create_alert(
                    message_id, brand_mentions, suspicious_patterns,
                    score, group_id, bot, alert_category='fraud'
                )
                if alert_data:
                    alerts.append(alert_data)
            
            # Brand mention alerts (informational warnings)
            elif brand_mentions and not suspicious_patterns:
                logger.debug("Creating brand mention alert", message_id=message_id)
                alert_data = await self._create_alert(
                    message_id, brand_mentions, [],
                    score, group_id, bot, alert_category='brand_info'
                )
                if alert_data:
                    alerts.append(alert_data)
            
            logger.info(
                "Message analyzed",
                message_id=message_id,
                brand_mentions=len(brand_mentions),
                suspicious_score=score,
                alerts_generated=len(alerts)
            )
            
            return {
                'alerts': alerts,
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error("Message analysis failed", error=str(e), message_id=message_id)
            return {'alerts': [], 'analysis': {'brand_mentions': [], 'suspicious_score': 0}}
    
    def _detect_brand_mentions(self, text_lower: str) -> List[str]:
        """Detect brand mentions in text."""
        mentions = []
        
        for keyword in self.brand_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                mentions.append(keyword)
        return mentions
    
    def _detect_suspicious_patterns(self, text: str) -> List[str]:
        """Detect suspicious patterns in text."""
        found = []
        for pattern, desc in self.suspicious_patterns.items():
            if pattern.search(text):
                found.append(desc)
        return found
    
    def _calculate_suspicious_score(self, brand_mentions: List[str], 
                                  suspicious_patterns: List[str], text_lower: str) -> float:
        """Calculate overall suspicious score."""
        score = 0.0
        
        # Brand mentions contribute, but capped
        score += min(len(brand_mentions), 2) * 0.2
        
        # Suspicious patterns, capped too
        score += min(len(suspicious_patterns), 3) * 0.3
        
        # Specific high-risk combinations
        if brand_mentions and suspicious_patterns:
            score += 0.4  # High risk when brands + suspicious patterns
        
        # Text length and urgency indicators
        if any(word in text_lower for word in ['urgent', 'immediate', 'expire', 'suspended']):
            score += 0.2
        
        # Cap score at 1.0
        return min(score, 1.0)
    
    async def _create_alert(self, message_id: int, brand_mentions: List[str], 
                          suspicious_patterns: List[str], score: float, 
                          group_id: int = None, bot = None, alert_category: str = 'fraud') -> Optional[Dict[str, Any]]:
        """Create fraud alert if conditions are met."""
        try:                
            if alert_category == 'brand_info':
                alert_type = "brand_mention_info"
            else:
                alert_type = "fraud_detection"
                if brand_mentions and suspicious_patterns:
                    alert_type = "high_risk_fraud"
                elif brand_mentions:
                    alert_type = "brand_mention"
                elif suspicious_patterns:
                    alert_type = "suspicious_content"
            
            alert_data = {
                'message_id': message_id,
                'alert_type': alert_type,
                'keywords_found': brand_mentions + suspicious_patterns,
                'confidence_score': score,
                'status': 'pending'
            }
            
            alert_id = await db_manager.create_alert(alert_data)
            
            # Send warning message to the group if bot is available
            if bot and group_id:
                await self._send_warning_message(bot, group_id, alert_type, score, brand_mentions + suspicious_patterns, alert_category)
                
            return {
                'id': alert_id,
                'type': alert_type,
                'score': score,
                'keywords': brand_mentions + suspicious_patterns
            }
            
        except Exception as e:
            logger.error("Failed to create alert", error=str(e), message_id=message_id)
            return None
    
    async def _send_warning_message(self, bot, group_id: int, alert_type: str, score: float, keywords: List[str], alert_category: str = 'fraud'):
        """Send warning message to the group where suspicious activity was detected."""
        try:
            # Create warning message based on alert category and type
            if alert_category == 'brand_info':
                # Gentle informational message for brand mentions
                warning_message = f"""
🔍 BRAND MENTION DETECTED

📋 Brand(s): {', '.join(keywords) if keywords else 'Financial brand'}
ℹ️ Notice: A financial brand was mentioned in this conversation.

🛡️ Security Reminder: Always verify financial requests through official channels.
💡 Tip: Be cautious of unsolicited financial offers or requests.

📞 Questions? Contact group administrators if needed.
                """.strip()
            else:
                # Critical warning message for fraud alerts
                warning_emoji = self._get_warning_emoji(alert_type, score)
                severity = self._get_severity_level(score)
                
                warning_message = f"""
{warning_emoji} FRAUD DETECTION ALERT {warning_emoji}

🔍 Severity: {severity}
📊 Risk Score: {score:.1f}/1.0
🏷️ Alert Type: {alert_type.replace('_', ' ').title()}

⚠️ Detected Patterns: {', '.join(keywords) if keywords else 'Suspicious activity'}

🛡️ Security Notice: This message has been flagged for potential fraudulent content. Please exercise caution and verify any financial requests independently.

📞 Report: If you believe this is a false positive, please contact group administrators.
                """.strip()
            
            # Send the warning message (no parse_mode to avoid formatting issues)
            await bot.send_message(
                chat_id=group_id,
                text=warning_message
            )
            
            logger.info(
                "Warning message sent to group",
                group_id=group_id,
                alert_type=alert_type,
                alert_category=alert_category,
                score=score
            )
            
        except Exception as e:
            logger.error(
                "Failed to send warning message",
                error=str(e),
                group_id=group_id,
                alert_type=alert_type
            )
    
    def _get_warning_emoji(self, alert_type: str, score: float) -> str:
        """Get appropriate warning emoji based on alert type and score."""
        if score >= 0.9 or alert_type == "high_risk_fraud":
            return "🚨"
        elif score >= 0.7:
            return "⚠️"
        else:
            return "🔍"
    
    def _get_severity_level(self, score: float) -> str:
        """Get severity level based on score."""
        if score >= 0.9:
            return "CRITICAL"
        elif score >= 0.7:
            return "HIGH"
        elif score >= 0.5:
            return "MEDIUM"
        else:
            return "LOW"


# Global fraud detector instance
fraud_detector = FraudDetector()

